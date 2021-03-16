import io
import cv2

import numpy as np

def plt_to_img(fig):
    """
    Writes the figure to a raw image in memory.
    
    Returns the in-memory image
    """
    # TODO: For whatever reason, the plot introduces a large border with alpha 0. Fix that
    io_buf = io.BytesIO()
    fig.savefig(io_buf, format='raw')
    io_buf.seek(0)
    new_shape =(int(fig.bbox.bounds[3]), int(fig.bbox.bounds[2]), -1)
    mem_img = np.reshape(np.frombuffer(io_buf.getvalue(), dtype=np.uint8), newshape=new_shape)
    # Drop all pixels with 0 in the alpha channel.
    mem_img = mem_img[:,:,:3]
    io_buf.close()
    return mem_img

def imgs_to_video(imgs, out_path, framerate=30):
    """
    Convert a series of png encoded images into a video using the MJPEG codec.
    Ensure that all imgs are 2d np ararys of the same dimension!
    
    out_path - The path to write the video to.
    framerate - The framerate of the resulting video. Defaults to 30
    """
    frame_h, frame_w, _ = imgs[0].shape
    out = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"MJPG"), framerate, (frame_w,frame_h))
    for img in imgs:
        # TRICKY: OpenVC has images in BGR, not RGB. Convert here
        bgr_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        out.write(bgr_img)
    out.release()
