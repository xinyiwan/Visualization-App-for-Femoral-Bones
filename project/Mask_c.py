import numpy as np

class Mask:

    def __init__(self, img):
        """ Build mask

        -- img: the image need to be masked 
        """

        self.size = img.shape
        self.check = np.zeros(img.shape)
        self.img = img

    def reset_checked(self):
        self.checked = np.zeros(self.img.shape)

    def segment(self, x, up, down):

        y = self.size[0]
        z = self.size[2]

        seg = np.zeros(self.img.shape)

        for i in range(y):
            for j in range(x - up, x + down):
                for k in range(z):

                    if self.img[i,j,k] == 0:
                        continue

                    if self.img[i,j,k] >= 0 and self.checked[i,j,k] == 0:
                        seg[i,j,k] = self.img[i,j,k]
                        self.checked[i,j,k] = 1

        return seg
