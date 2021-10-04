def imshow(title, img):
    import cv2
    try:
        cv2.imshow(title, img)
        cv2.waitKey()
    finally:
        cv2.destroyAllWindows()
