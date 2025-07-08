import math
import numpy as np  # 导入numpy库，用于处理数组和矩阵
from sklearn.preprocessing import MinMaxScaler
from scipy.signal import savgol_filter
from sklearn.decomposition import PCA

def cut_data(raw_datas):
    """
    找出二维数组中最短的子数组，并将所有子数组的长度修剪为最短子数组的长度。
    
    参数:
    arr (list of list): 输入的二维数组
    
    返回:
    list of list: 修剪后的二维数组
    """
    # 找出最短的子数组长度
    min_length = min(len(sub_arr) for sub_arr in raw_datas)
    
    # 修剪所有子数组到最短长度
    trimmed_datas = [sub_arr[:min_length] for sub_arr in raw_datas]
    
    return trimmed_datas

#减去暗电流
def Subtract_dark_current(column_data):
        #这两个循环的作用是减去一组数据中的最小值，相当于减去暗电流，用于增加对比度    
        min = 1   #定义一个大值用于存储一组数据中的最小值
        for i in range(len(column_data)):
            if column_data[i] < float(min):
                min = column_data[i]
        for j in range(len(column_data)):
            column_data[j] = pow((column_data[j] - min)*10e9,1)
        return column_data

#归一化
def Normalized_data(column_data):
    for i in range(len(column_data)):
        arr = np.array(column_data[i]).reshape(-1, 1)  # 转换为二维数组，每行一个样本，每列一个特征
 
        scaler = MinMaxScaler()
        scaled_arr = scaler.fit_transform(arr)
        scaled_arr = [math.pow(item,1.5) for item in scaled_arr]
        column_data[i] = scaled_arr

    return column_data



#采样计算          
def data_sampling(data,n_out):
    """
    使用Largest Triangle Three Buckets算法下采样数据。
    data: 形如[(x0, y0), (x1, y1), ..., (xn, yn)]的数组
    n_out: 输出数据的点数
    """

    indnx = np.arange(len(data))
    data = np.column_stack((indnx,data))

    # data = np.array(data)
    if n_out >= len(data):
        return data
    if n_out <= 2:
        return data[:n_out]
    
    n_buckets = n_out - 2
    bucket_size = (len(data) - 2) / n_buckets
    sampled = [data[0]]
    
    for i in range(n_buckets):
        start = int(1 + i * bucket_size)
        end = int(1 + (i + 1) * bucket_size)
        if i == n_buckets - 1:
            end = len(data) - 1
        
        next_start = end
        next_end = int(1 + (i + 2) * bucket_size)
        if next_end >= len(data):
            next_end = len(data) - 1
            
        next_bucket = data[next_start:next_end + 1]
        next_point = data[end] if len(next_bucket) == 0 else next_bucket[0]
        bucket = data[start:end + 1]
            
        max_area = -1
        selected_point = bucket[0]
        for point in bucket:
            a = sampled[-1]
            b = point
            c = next_point
            area = abs((a[0]*(b[1]-c[1]) + b[0]*(c[1]-a[1]) + c[0]*(a[1]-b[1])) / 2)
            if area > max_area:
                max_area = area
                selected_point = point
        sampled.append(selected_point)
        
    sampled.append(data[-1])
    sampled = np.array(sampled)
    sampled = sampled[:,1].tolist()
    return sampled

# 控制数据长度，通过均值将长数据分为length份
def process_data(data_points, length):
    # NOTE: 将长数据等份划分为length个数据点，如果数据少于length个，用-1补齐
    if len(data_points) > length:  # 如果数据点的长度大于length
        chunk_size = len(data_points) // length  # 计算每个等份的大小
        return [np.mean(data_points[i * chunk_size:(i + 1) * chunk_size]) for i in range(length)]  # 返回每个等份的均值
    elif len(data_points) < length:  # 如果数据点的长度小于length
        # NOTE: 用零补齐到length个数据点
        return np.pad(data_points, (0, length - len(data_points)), 'constant', constant_values=-1)  # 用-1补齐
    return data_points  # 如果数据点长度等于length，直接返回原数据           


# 均方根计算
def rms_downsample(data, length):
    """
    将任意长度数据通过均方根计算降采样到指定点数
    
    参数：
    data : 输入数据（列表或numpy数组）
    length : 目标数据点数（必须小于原始数据长度）
    
    返回：
    numpy数组包含降采样后的m个RMS值
    """
    data = np.asarray(data)
    n = len(data)
    
    if length >= n:
        raise ValueError("目标数据点数必须小于原始数据长度")
    if length <= 0:
        raise ValueError("目标数据点数必须大于0")

    # 将数据分成m个分组（允许最后分组长度不同）
    groups = np.array_split(data, length)
    
    # 计算每个分组的RMS值
    rms_values = [np.sqrt(np.mean(group**2)) for group in groups]
    
    return np.array(rms_values)


# 最大最小值取值
def reduce_data(data, target_length, method):
    n = len(data)
    k = target_length
    base, remainder = divmod(n, k)
    sizes = [base + 1] * remainder + [base] * (k - remainder)
    indices = np.cumsum(sizes[:-1])
    chunks = np.split(data, indices)
    
    if method == 'max':
        reduced = [np.max(chunk) for chunk in chunks]
    elif method == 'mean':
        reduced = [np.mean(chunk) for chunk in chunks]
    else:
        raise ValueError("Method must be 'max' or 'mean'")
    return np.array(reduced)


# 新增方法
def reduce_data_median(data, target_length):
    """使用中值缩减数据长度"""
    original_length = len(data)
    step = max(1, original_length // target_length)
    reduced = []
    
    for i in range(0, original_length, step):
        segment = data[i:i+step]
        if segment:
            reduced.append(np.median(segment))
    
    return reduced[:target_length]

def exponential_moving_average(data, target_length, alpha=0.3):
    """指数加权移动平均"""
    if len(data) <= target_length:
        return data
    
    # 计算平滑因子
    smoothed = [data[0]]
    for i in range(1, len(data)):
        smoothed.append(alpha * data[i] + (1 - alpha) * smoothed[-1])
    
    # 降采样到目标长度
    step = len(smoothed) // target_length
    return [smoothed[i] for i in range(0, len(smoothed), step)][:target_length]

def wavelet_denoise(data, target_length, wavelet='db4', level=3):
    """小波变换降噪"""
    # 执行小波变换
    coeffs = pywt.wavedec(data, wavelet, level=level)
    
    # 阈值处理（去噪）
    threshold = np.std(coeffs[-level]) * np.sqrt(2 * np.log(len(data)))
    coeffs = [pywt.threshold(c, threshold, mode='soft') for c in coeffs]
    
    # 重构信号
    denoised = pywt.waverec(coeffs, wavelet)
    
    # 确保长度一致
    denoised = denoised[:len(data)]
    
    # 降采样到目标长度
    step = len(denoised) // target_length
    return [denoised[i] for i in range(0, len(denoised), step)][:target_length]

def savgol_smoothing(data, target_length, window_length=15, polyorder=2):
    """Savitzky-Golay滤波"""
    if len(data) < window_length:
        window_length = len(data) // 2 or 1
    
    smoothed = savgol_filter(data, window_length, polyorder)
    
    # 降采样到目标长度
    step = len(smoothed) // target_length
    return [smoothed[i] for i in range(0, len(smoothed), step)][:target_length]

def pca_reduction(data, target_length):
    """主成分分析降维"""
    # 将数据转为2D数组
    data_2d = np.array(data).reshape(-1, 1)
    
    # 应用PCA
    pca = PCA(n_components=min(target_length, len(data_2d)))
    transformed = pca.fit_transform(data_2d)
    
    # 取第一主成分
    return transformed[:, 0].tolist()[:target_length]

def update_heatmap(data_matrix, new_data, length, data_groups):
    """
    更新热图数据矩阵
    
    Args:
        data_matrix (np.array): 数据矩阵
        new_data (list): 新数据序列
        length (int): 数据长度
        data_groups (int): 数据组数
    
    Returns:
        np.array: 更新后的数据矩阵
    """
    # 确保数据长度匹配
    if len(new_data) != length:
        # 如果数据长度不足，用0填充
        if len(new_data) < length:
            padded_data = np.pad(new_data, (0, length - len(new_data)), 'constant')
        # 如果数据长度超过，截断
        else:
            padded_data = new_data[:length]
    else:
        padded_data = new_data
    
    # 将新数据添加到数据矩阵的最后一行
    updated_matrix = np.vstack([data_matrix, padded_data])
    
    # 如果数据矩阵超过data_groups行，则移除最旧的行
    if updated_matrix.shape[0] > data_groups:
        updated_matrix = updated_matrix[-data_groups:, :]
    
    return updated_matrix


if __name__ == "__main__":
    Subtract_dark_current()
    process_data()
    Normalized_data()
    cut_data()