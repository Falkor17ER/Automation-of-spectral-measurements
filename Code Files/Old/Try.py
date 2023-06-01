import matplotlib.pyplot as plt

fig, ax = plt.subplots()
peaks_y = [1, 2, 3]
peaks_x = [4, 5, 6]
ax.scatter(peaks_y, peaks_x, marker='o', color='blue', s=100)

# add red dots
red_dots = ax.scatter(peaks_y, peaks_x, marker='o', color='red', s=100)

# remove the red dots
plt.show()

red_dots.remove()

plt.show()
