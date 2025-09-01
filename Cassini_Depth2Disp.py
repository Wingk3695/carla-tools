import os
import cv2
import numpy as np
import math
import torch
import torch.nn.functional as F
from numba import jit

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 主要步骤：
# 1. 采集视角1-4的全景彩色图像以及全景深度图，图像坐标一律朝向前方，即满足相机12立体匹配方向
# 2. 构造6对立体匹配彩色图像对，分别调用erp2rect_cassini将ERP全景图转为Cassini投影立体图像对
# 3. 构造立体匹配对Cassini深度图：
#   3.1. 若采集每个视角的全景ERP深度，则对相应视角深度图调用erp2rect_cassini转化即可（与立体匹配中左图构造一致）
#   3.2. 若只采集了相机1的全景ERP深度，则先转化为相机1无旋转条件下的Cassini深度，再调用CassiniDepthViewTrans，转化到其他视角和朝向
# 4. 构造立体匹配对Cassini视差图，将步骤3产生的6个Cassini深度，调用Cassini_depth2dispNumpy转为视差

# 各视角平移旋转，从相机1到各个立体图像对
# y0, z0, x0, pitch, yaw, roll
cam_pair_dict = {'12': 0, '13': 1, '14': 2, '23': 3, '24': 4, '34': 5}
baselines=np.array([1, 1, math.sqrt(2), math.sqrt(2), 1, 1])
ext_params=np.array([
  [0,    0,    0,    0,    0,    0],# 12: 无平移，无旋转
  [0,    0,    0,    -0.5 * math.pi, 0, 0],#13：无平移，顺时针旋转90度
  [0,    0,    0,    -0.25 * math.pi, 0, 0],#14：无平移，顺时针旋转45度
  [0,    0,    -1.0,    -0.75 * math.pi, 0, 0],#23：先向右平移1米到达相机2，再顺时针旋转135度
  [0,    0,    -1.0,    -0.5 * math.pi, 0, 0],#24：先向右平移1米到达相机2，再顺时针旋转90度
  [0,    -1.0,    0,    0, 0, 0]#34：先向后平移1米到达相机3，无旋转
])

def get_Rotate_matrix_shift(ext_p):
  y0, z0, x0, pitch, yaw, roll = ext_p
  Rx = np.array([[1, 0, 0], [0, np.cos(roll), -np.sin(roll)], [0, np.sin(roll), np.cos(roll)]])
  Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
  Ry = np.array([[np.cos(pitch), 0, -np.sin(pitch)], [0, 1, 0], [np.sin(pitch), 0, np.cos(pitch)]])
  R = np.dot(np.dot(Rx, Rz), Ry)
  t = np.array([[x0], [y0], [z0]])
  return R,t
# ERP转Cassini
# 输入参数：erp图像，旋转矩阵（改变图像朝向，使满足立体匹配需要），Cassini图像高和宽
def erp2rect_cassini(erp, R, ca_h, ca_w):
  # erp: erp image
  # R: rotate matrix
  # ca_h,ca_w: Cassini shape(height, width)
  erp_h, erp_w = erp.shape[:-1]
  logger.debug(f"ERP shape: {erp_h}x{erp_w}, Cassini shape: {ca_h}x{ca_w}")

  if erp.ndim == 2:
    erp = np.expand_dims(erp, axis=-1)
    source_image = torch.FloatTensor(erp).unsqueeze(0).transpose(1, 3).transpose(2, 3).cuda()
  elif erp.ndim == 3:
    source_image = torch.FloatTensor(erp).unsqueeze(0).transpose(1, 3).transpose(2, 3).cuda()
  else:
    source_image = erp

  theta_ca_start = np.pi - (np.pi / ca_h)
  theta_ca_end = -np.pi
  theta_ca_step = 2 * np.pi / ca_h
  theta_ca_range = np.arange(theta_ca_start, theta_ca_end, -theta_ca_step)
  theta_ca_map = np.array([theta_ca_range for i in range(ca_w)]).astype(np.float32).T

  phi_ca_start = 0.5 * np.pi - (0.5 * np.pi / ca_w)
  phi_ca_end = -0.5 * np.pi
  phi_ca_step = np.pi / ca_w
  phi_ca_range = np.arange(phi_ca_start, phi_ca_end, -phi_ca_step)
  phi_ca_map = np.array([phi_ca_range for j in range(ca_h)]).astype(np.float32)

  x = np.sin(phi_ca_map)
  y = np.cos(phi_ca_map) * np.sin(theta_ca_map)
  z = np.cos(phi_ca_map) * np.cos(theta_ca_map)

  X = np.expand_dims(np.dstack((x, y, z)), axis=-1)
  X2 = np.matmul(np.linalg.inv(R), X)
  logger.debug(f"X2 shape: {X2.shape}, X2[:, :, 0, :].shape: {X2[:, :, 0, :].shape}")
  phi_erp_map = np.arcsin(X2[:, :, 1, :])  #arcsin(y)
  theta_erp_map = np.arctan2(X2[:, :, 0, :], X2[:, :, 2, :])  #arctan(x/z)

  grid_x = torch.FloatTensor(np.clip(-theta_erp_map / np.pi, -1, 1)).cuda()
  grid_y = torch.FloatTensor(np.clip(-phi_erp_map / (0.5 * np.pi), -1, 1)).cuda()
  grid = torch.cat([grid_x, grid_y], dim=-1).unsqueeze(0).repeat_interleave(source_image.shape[0], dim=0)
  sampled_image = F.grid_sample(source_image, grid, mode='bilinear', align_corners=True, padding_mode='border')  # 1, ch, self.output_h, self.output_w
  if erp.ndim == 3:
    erp = sampled_image.transpose(1, 3).transpose(1, 2).data.cpu().numpy()[0].astype(erp.dtype)
    return erp.squeeze()
  else:
    erp = sampled_image
    return erp.squeeze(1)

# Cassini深度投影变换，用于将相机1位置的Cassini深度图转化为不同立体匹配图像对所需的左图深度
# 输入参数 view_1是相机1Cassini深度图，其余参数为转化相对外参，包含平移距离和旋转角度，参照ext_params
def CassiniDepthViewTrans(view_1, y0, z0, x0, pitch, yaw, roll):
  Rx = np.array([[1, 0, 0], [0, np.cos(roll), -np.sin(roll)], [0, np.sin(roll), np.cos(roll)]])

  Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])

  Ry = np.array([[np.cos(pitch), 0, -np.sin(pitch)], [0, 1, 0], [np.sin(pitch), 0, np.cos(pitch)]])

  R = np.dot(np.dot(Rx, Rz), Ry)

  t = np.array([[x0], [y0], [z0]])

  output_h = view_1.shape[0]
  output_w = view_1.shape[1]

  theta_1_start = np.pi - (np.pi / output_h)
  theta_1_end = -np.pi
  theta_1_step = 2 * np.pi / output_h
  theta_1_range = np.arange(theta_1_start, theta_1_end, -theta_1_step)
  theta_1_map = np.array([theta_1_range for i in range(output_w)]).astype(np.float32).T

  phi_1_start = 0.5 * np.pi - (0.5 * np.pi / output_w)
  phi_1_end = -0.5 * np.pi
  phi_1_step = np.pi / output_w
  phi_1_range = np.arange(phi_1_start, phi_1_end, -phi_1_step)
  phi_1_map = np.array([phi_1_range for j in range(output_h)]).astype(np.float32)

  r_1 = view_1

  x_1 = r_1 * np.sin(phi_1_map)
  y_1 = r_1 * np.cos(phi_1_map) * np.sin(theta_1_map)
  z_1 = r_1 * np.cos(phi_1_map) * np.cos(theta_1_map)
  X_1 = np.expand_dims(np.dstack((x_1, y_1, z_1)), axis=-1)

  X_2 = np.matmul(R, X_1 - t)

  r_2 = np.sqrt(np.square(X_2[:, :, 0, 0]) + np.square(X_2[:, :, 1, 0]) + np.square(X_2[:, :, 2, 0]))
  theta_2_map = np.arctan2(X_2[:, :, 1, 0], X_2[:, :, 2, 0])
  phi_2_map = np.arcsin(np.clip(X_2[:, :, 0, 0] / r_2, -1, 1))

  view_2 = np.ones((output_h, output_w)).astype(np.float32) * 100000

  I_2 = np.clip(np.rint(output_h / 2 - output_h * theta_2_map / (2 * np.pi)), 0, output_h - 1).astype(np.int16)
  J_2 = np.clip(np.rint(output_w / 2 - output_w * phi_2_map / np.pi), 0, output_w - 1).astype(np.int16)

  view_2 = __iterPixels_with_conf(output_h, output_w, r_1, r_2, view_2, I_2, J_2)

  view_2[view_2 == 100000] = 0
  view_2 = view_2.astype(np.float32)
  view_2[view_2 > 1000] = 1000

  return view_2


@jit(nopython=True)
def __iterPixels_with_conf(output_h, output_w, r_1, r_2, view_2, I_2, J_2):
  for i in range(output_h):
    for j in range(output_w):
      if r_1[i, j] > 0:
        flag = r_2[i, j] < view_2[I_2[i, j], J_2[i, j]]
        view_2[I_2[i, j], J_2[i, j]] = flag * r_2[i, j] + (1 - flag) * view_2[I_2[i, j], J_2[i, j]]
  return view_2

# Cassini 投影下深度图转视差图，视角位置和方向不变（即无旋转或平移变换）
# 参数：输入深度图, Cassini投影图像高、宽，最大视差值，最大深度值，基线（相机间距离）
# 基线设置：
# 对于相机对（12,13,24,34）基线为1米（正方形边长）
# 对于相机对（14,23）基线为sqrt(2)米（正方形对角线）
# 该方法不改变深度图和视差图对应外参，需要先将深度图转化为双目中左图的位置和角度

def Cassini_depth2dispNumpy(depthMap,height, width, maxDisp, maxDepth, baseline):
    # input: depth map,1-channel numpy array, shape(h,w)
    # output: disp map,1-channel numpy array, shape(h,w)
    h, w = depthMap.shape
    assert h == height and w == width, "request shape is ({},{}), while input shape is ({},{})".format(height, width, h, w)
    invMask = (depthMap <= 0) | (depthMap > maxDepth)
    depth_not_0 = np.ma.array(depthMap, mask=invMask)
    phi_1_start = 0.5 * math.pi - (0.5 * math.pi / width)
    phi_1_end = -0.5 * math.pi
    phi_1_step = math.pi / width
    phi_1_range = np.arange(phi_1_start, phi_1_end, -phi_1_step)
    phi_l_map = np.array([phi_1_range for j in range(height)]).astype(np.float32)
    disp = width * (np.arcsin(
        np.clip(
            (depth_not_0 * np.sin(phi_l_map) + baseline) / np.sqrt(depth_not_0 * depth_not_0 + baseline * baseline - 2 * depth_not_0 * baseline * np.cos(phi_l_map + np.pi / 2)),
            -1,
            1)) - phi_l_map) / np.pi
    disp = disp.filled(np.nan)
    disp[depthMap >= maxDepth] = 0
    disp[disp < 0] = 0
    return disp

# 对应的Disp转Depth
def Cassini_disp2depthNumpy(dispMap, height, width, maxDisp, maxDepth, baseline):
    h, w = dispMap.shape
    assert h == height and w == width, "request shape is ({},{}), while input shape is ({},{})".format(height, width, h, w)
    phi_1_start = 0.5 * math.pi - (0.5 * math.pi / width)
    phi_1_end = -0.5 * math.pi
    phi_1_step = math.pi / width
    phi_1_range = np.arange(phi_1_start, phi_1_end, -phi_1_step)
    phi_l_map = np.array([phi_1_range for j in range(height)]).astype(np.float32)
    mask_disp_is_0 = dispMap == 0
    disp_not_0 = np.ma.array(dispMap, mask=mask_disp_is_0)
    phi_r_map = disp_not_0 * math.pi / width + phi_l_map
    # sin theory
    depth_l = baseline * np.sin(math.pi / 2 - phi_r_map) / np.sin(phi_r_map - phi_l_map)
    depth_l = depth_l.filled(maxDepth)
    depth_l[depth_l > maxDepth] = maxDepth
    depth_l[depth_l < 0] = 0
    return depth_l

if __name__ == '__main__':
  # NOTE: depth->disp->depth testing
  # 读取Cassini深度
  depthName = './002430_depth.npz'
  depthGT = np.load(depthName)['arr_0'].astype(np.float32)
  # 转视差
  dispGT = Cassini_depth2dispNumpy(depthGT,height=1024, width=512, maxDisp=192, maxDepth=1000, baseline=1.0)
  np.savez('./002430_12_disp.npz',arr_0=dispGT)
  # 视差转回深度，校验误差
  depthback = Cassini_disp2depthNumpy(dispGT,height=1024, width=512, maxDisp=192, maxDepth=1000, baseline=1.0)
  np.save('depthback.npy', depthback.astype(np.float32))
  print(np.mean(np.abs(depthGT - depthback) / depthGT))
