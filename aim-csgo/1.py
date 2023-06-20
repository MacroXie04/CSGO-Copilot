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
