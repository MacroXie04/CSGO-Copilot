from grabscreen import grab_screen
from cs_model import load_model
import cv2
import win32gui
import win32con
import torch
import numpy as np
from utils.general import non_max_suppression, scale_coords, xyxy2xywh
from utils.augmentations import letterbox
import pynput
from mouse_control import lock, recoil_control
from threading import Thread
import argparse

##此区域为调试模块 执行前需按照标砖设置参数
parser = argparse.ArgumentParser()
parser.add_argument('--model-path', type=str, default='./models/aim-csgo2.pt')
parser.add_argument('--imgsz', type=int, default=640)
parser.add_argument('--conf-thres', type=float, default=0.4)
parser.add_argument('--iou-thres', type=float, default=0.05)
parser.add_argument('--use-cuda', type=bool, default=True)
parser.add_argument('--color', type=tuple, default=(0, 255, 0))
parser.add_argument('--thickness', type=int, default=3)
parser.add_argument('--show-window', type=bool, default=True)


parser.add_argument('--fullscreen-detect', type=bool, default=True)
parser.add_argument('--resolution', type=tuple, default=(1920, 1080))

parser.add_argument('--region', type=tuple, default=(0, 0, 1920, 1080))

parser.add_argument('--hold-lock', type=bool, default=False)
parser.add_argument('--lock-button', type=str, default='shift')
parser.add_argument('--head-first', type=bool, default=True)
parser.add_argument('--lock-tag', type=list, default=[0, 1, 2, 3])
parser.add_argument('--lock-choice', type=list, default=[0, 1, 2, 3])

parser.add_argument('--recoil-button', type=str, default='x1')
parser.add_argument('--recoil-sen', type=float, default=-2)

args = parser.parse_args()

'------------------------------------------------------------------------------------'
4

args.lock_tag = [str(i) for i in args.lock_tag]
args.lock_choice = [str(i) for i in args.lock_choice]

device = 'cuda' if args.use_cuda else 'cpu'
half = device != 'cpu'
imgsz = args.imgsz

conf_thres = args.conf_thres
iou_thres = args.iou_thres

if args.fullscreen_detect:
    top_x, top_y = 0, 0
    x, y = args.resolution
    len_x, len_y = args.resolution
else:
    top_x, top_y, x, y = args.region
    len_x, len_y = args.region[2] - args.region[0], args.region[3] - args.region[1]

model = load_model(args)
stride = int(model.stride.max())
names = model.module.names if hasattr(model, 'module') else model.names

lock_mode = False
mouse = pynput.mouse.Controller()

t = Thread(target=recoil_control, kwargs={'args': args})
t.start()

cv2.namedWindow('csgo-detect', cv2.WINDOW_NORMAL)
cv2.resizeWindow('csgo-detect', len_x // 3, len_y // 3)

with pynput.mouse.Events() as events:
    print('enjoy yourself!')
    while True:
        it = next(events)
        while it is not None and not isinstance(it, pynput.mouse.Events.Click):
            it = next(events)
        if args.hold_lock:
            if it is not None and it.button == eval('it.button.' + args.lock_button) and it.pressed:
                lock_mode = True
                print('lock mode on')
            if it is not None and it.button == eval('it.button.' + args.lock_button) and not it.pressed:
                lock_mode = False
                print('lock mode off')
        else:
            if it is not None and it.button == eval('it.button.' + args.lock_button) and it.pressed:
                lock_mode = not lock_mode
                print('lock mode', 'on' if lock_mode else 'off')

        img0 = grab_screen(region=(top_x, top_y, x, y))
        img0 = cv2.resize(img0, (len_x, len_y))

        img = letterbox(img0, imgsz, stride=stride)[0]

        img = img.transpose((2, 0, 1))[::-1]
        img = np.ascontiguousarray(img)

        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()
        img /= 255.

        if len(img.shape) == 3:
            img = img[None] # img = img.unsqueeze(0)

        pred = model(img, augment=False, visualize=False)[0]
        pred = non_max_suppression(pred, conf_thres, iou_thres, agnostic=False)

        aims = []
        for i, det in enumerate(pred):
            gn = torch.tensor(img0.shape)[[1, 0, 1, 0]]
            if len(det):
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()

                for *xyxy, conf, cls in reversed(det):
                    # bbox:(tag, x_center, y_center, x_width, y_width)
                    """
                    0 ct_head  1 ct_body  2 t_head  3 t_body
                    """
                    xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                    line = (cls, *xywh)  # label format
                    aim = ('%g ' * len(line)).rstrip() % line
                    aim = aim.split(' ')
                    # print(aim)
                    aims.append(aim)

            if len(aims):
                if lock_mode:
                    lock(aims, mouse, top_x, top_y, len_x, len_y, args)
                for i, det in enumerate(aims):
                    _, x_center, y_center, width, height = det
                    x_center, width = len_x * float(x_center), len_x * float(width)
                    y_center, height = len_y * float(y_center), len_y * float(height)
                    top_left = (int(x_center - width / 2.), int(y_center - height / 2.))
                    bottom_right = (int(x_center + width / 2.), int(y_center + height / 2.))
                    color = args.color # RGB
                    cv2.rectangle(img0, top_left, bottom_right, color, thickness=args.thickness)

        cv2.imshow('csgo-detect', img0)

        hwnd = win32gui.FindWindow(None, 'csgo-detect')
        CVRECT = cv2.getWindowImageRect('csgo-detect')
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break