##鼠标控制单元

import pynput
import csv
import time

def lock(aims, mouse, top_x, top_y, len_x, len_y, args):
    mouse_pos_x, mouse_pos_y = mouse.position
    aims_copy = aims.copy()
    aims_copy = [x for x in aims_copy if x[0] in args.lock_choice]
    if len(aims_copy):
        dist_list = []
        tag_list = [x[0] for x in aims_copy]
        if args.head_first:
            if args.lock_tag[0] in tag_list or args.lock_tag[2] in tag_list:
                aims_copy = [x for x in aims_copy if x[0] in [args.lock_tag[0], args.lock_tag[2]]]
        for det in aims_copy:
            _, x_c, y_c, _, _ = det
            dist = (len_x * float(x_c) + top_x - mouse_pos_x) ** 2 + (len_y * float(y_c) + top_y - mouse_pos_y) ** 2
            dist_list.append(dist)

        det = aims_copy[dist_list.index(min(dist_list))]

        tag, x_center, y_center, width, height = det
        x_center, width = len_x * float(x_center) + top_x, len_x * float(width)
        y_center, height = len_y * float(y_center) + top_y, len_y * float(height)
        if tag in [args.lock_tag[0], args.lock_tag[2]]:
            mouse.position = (x_center, y_center)
        elif tag in [args.lock_tag[1], args.lock_tag[3]]:
            mouse.position = (x_center, y_center - 1 / 6 * height)


def recoil_control(args):
    f = csv.reader(open('./ammo_path/ak47.csv', encoding='utf-8'))
    ak_recoil = []
    for i in f:
        ak_recoil.append(i)
    ak_recoil[0][0] = '0'
    ak_recoil = [[float(i) for i in x] for x in ak_recoil]
    k = args.recoil_sen
    mouse = pynput.mouse.Controller()
    flag = 0
    recoil_mode = False # mouse.button.x1
    with pynput.mouse.Events() as events:
        for event in events:
            if isinstance(event, pynput.mouse.Events.Click):
                if event.button == event.button.left:
                    if event.pressed:
                        flag = 1
                    else:
                        flag = 0
                if event.button == eval('event.button.' + args.recoil_button) and event.pressed:
                    recoil_mode = not recoil_mode
                    print('recoil mode', 'on' if recoil_mode else 'off')

            if flag and recoil_mode:
                i = 0
                a = next(events)
                while True:
                    mouse.move(-ak_recoil[i][0] * k, ak_recoil[i][1] * k)
                    i += 1
                    if i == 30:
                        break
                    if a is not None and isinstance(a, pynput.mouse.Events.Click) and a.button == a.button.left and not a.pressed:
                        break
                    a = next(events)
                    while a is not None and not isinstance(a, pynput.mouse.Events.Click):
                        a = next(events)
                    time.sleep(ak_recoil[i][2] / 1000)
                flag = 0
