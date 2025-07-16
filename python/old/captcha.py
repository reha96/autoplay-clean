#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 15:42:13 2023

@author: reha.tuncer
"""


from PIL import ImageFont, ImageDraw, Image
import numpy as np
import pandas as pd
import random
import cv2
import textwrap
import string
from openpyxl import Workbook

sentences = []
longth = []
images = []
control = []
df = Workbook()
df.save(filename='captchas_list.xlsx')
ksize = (5,6)

np.random.seed(0)
# image generator
for i in range(100):
    img = np.zeros(shape=(300, 600, 3), dtype=np.uint8)
    W, H = (600, 300)
    img_pil = Image.fromarray(img+255)
    draw = ImageDraw.Draw(img_pil)

    # size = random.randint(20, 22)
    size = 24
    font = ImageFont.truetype("Monaco", size)
    # length = random.randint(400, 900)
    length = 35

    img = np.zeros(((size*2)+5, length*size, 3), np.uint8)

    # text = ''.join(random.sample(sorted(df2[0]),1))
    text = ''.join(
        random.choice(string.ascii_uppercase + string.digits + string.whitespace[0]*5 +
                      string.digits + string.ascii_lowercase)
        for _ in range(length))

    control.append(text)

    # divide length for number of lines (35 for 1 line, 5 for 7 lines)
    para = textwrap.wrap(text, width=35)

    current_h, pad = H/(len(para)+1), 10

    r = random.randint(0, 200)
    g = random.randint(0, 200)
    b = random.randint(0, 200)
    while r+g+b > 425:
        r = random.randint(0, 200)
        g = random.randint(0, 200)
        b = random.randint(0, 200)
    for line in para:
        w, h = draw.textsize(line, font=font)
        draw.text(((W-w)/2, current_h), line, font=font,
                  fill=(r, g, b))
        current_h += h + pad

    draw.line([(random.choice(range(W)), random.choice(range(H))), (random.choice(range(W)), random.choice(
        range(H)))], width=1, fill=(random.randint(0, 230), random.randint(0, 230), random.randint(0, 230)))
    draw.line([(random.choice(range(W)), random.choice(range(H))), (random.choice(range(W)), random.choice(
        range(H)))], width=1, fill=(random.randint(0, 230), random.randint(0, 230), random.randint(0, 230)))
    draw.line([(random.choice(range(W)), random.choice(range(H))), (random.choice(range(W)), random.choice(
        range(H)))], width=1, fill=(random.randint(0, 230), random.randint(0, 230), random.randint(0, 230)))
    draw.line([(random.choice(range(W)), random.choice(range(H))), (random.choice(range(W)), random.choice(
        range(H)))], width=1, fill=(random.randint(0, 230), random.randint(0, 230), random.randint(0, 230)))
    draw.line([(random.choice(range(W)), random.choice(range(H))), (random.choice(range(W)), random.choice(
        range(H)))], width=1, fill=(random.randint(0, 230), random.randint(0, 230), random.randint(0, 230)))

    img = np.array(img_pil)
    thresh = random.randint(1, 5)/100
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            rdn = random.random()
            if rdn < thresh:
                img[i][j] = random.randint(0, 123)
            elif rdn > 1-thresh:
                img[i][j] = random.randint(123, 255)
    # img = cv2.blur(img, (int(random.randint(4, 5)), int(random.randint(4, 5))))
    img = cv2.blur(img, ksize)
    images.append(img)
    Image.fromarray(img)

for i in range(len(images)):
    Image.fromarray(images[i]).save("trcp_"+str(i)+".jpeg")

df1 = pd.DataFrame(control)
with pd.ExcelWriter('captchas_list.xlsx', engine="openpyxl", mode='a') as writer:
    df1.to_excel(writer, header=False, index=False, sheet_name='captchas')
