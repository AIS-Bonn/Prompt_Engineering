import numpy as np

values = [
False, 13, 8.17, 6,
False, 15, 43.55, 7,
False, 11, 4.30, 5,
False, 13, 4.70, 6,
False, 17, 6.57, 8,
False, 17, 6.50, 8,
False, 13, 4.72, 6,
False, 13, 4.00, 6,
False, 11, 3.47, 5,
False, 17, 6.25, 8,
False, 13, 4.51, 6,
False, 11, 3.77, 5,
False, 13, 5.42, 6,
False, 13, 5.94, 6,
False, 13, 5.37, 6,
False, 13, 4.75, 6,
False, 11, 4.12, 5,
False, 11, 3.45, 5,
False, 17, 7.34, 8,
False, 13, 4.96, 6,
False, 11, 4.02, 5,
False, 17, 8.29, 8,
False, 13, 4.47, 6,
False, 13, 4.97, 6,
False, 11, 3.99, 5,
False, 7, 4.82, 3,
False, 11, 4.92, 5,
False, 11, 3.13, 5,
False, 11, 3.93, 5,
False, 11, 3.87, 5,
False, 15, 5.91, 7,
False, 13, 4.70, 6,
False, 7, 2.20, 3,
False, 13, 4.78, 6,
False, 17, 7.34, 8,
False, 13, 6.27, 6,
False, 13, 4.80, 6,
False, 11, 4.07, 5,
False, 13, 4.34, 6,
False, 11, 3.82, 5,
False, 11, 3.66, 5,
False, 13, 4.87, 6,
False, 13, 6.18, 6,
False, 13, 38.97, 6,
False, 17, 6.85, 8,
False, 13, 4.60, 6,
False, 11, 3.31, 5,
False, 13, 4.94, 6,
False, 13, 6.87, 6,
False, 11, 3.82, 5,
]

arrays = [[], [], [], []]

for i in range(len(values)):
    arrays[i % 4].append(values[i])
    
success_array = np.array(arrays[0])
length_array = np.array(arrays[1])
time_array = np.array(arrays[2])
num_fc_array = np.array(arrays[3])

print("----------")
print(f"Success avg: {np.mean(success_array)}")
print(f"Length avg: {np.mean(length_array)}; std: {np.std(length_array)}")
print(f"Time avg: {np.mean(time_array)}; std: {np.std(time_array)}")
print(f"Function calls avg: {np.mean(num_fc_array)}; std: {np.std(num_fc_array)}")
print("----------")
