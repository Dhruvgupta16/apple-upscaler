#include "fast_boxblur.h"
#include <stdlib.h>
#include <string.h>

void fast_box_blur_rgb(
    const uint8_t* src,
    uint8_t* dst,
    int width,
    int height,
    int radius
) {
    if (!src || !dst || width <= 0 || height <= 0 || radius <= 0) {
        if (src && dst && width > 0 && height > 0) {
            memcpy(dst, src, (size_t)width * height * 3);
        }
        return;
    }

    uint8_t* temp = (uint8_t*)malloc((size_t)width * height * 3);
    if (!temp) return;

    int div = 2 * radius + 1;

    // Horizontal pass
    for (int y = 0; y < height; ++y) {
        int r_acc = 0, g_acc = 0, b_acc = 0;
        int row_idx = y * width * 3;

        for (int i = -radius; i <= radius; ++i) {
            int px = i < 0 ? 0 : (i >= width ? width - 1 : i);
            r_acc += src[row_idx + px * 3 + 0];
            g_acc += src[row_idx + px * 3 + 1];
            b_acc += src[row_idx + px * 3 + 2];
        }

        for (int x = 0; x < width; ++x) {
            temp[row_idx + x * 3 + 0] = (uint8_t)(r_acc / div);
            temp[row_idx + x * 3 + 1] = (uint8_t)(g_acc / div);
            temp[row_idx + x * 3 + 2] = (uint8_t)(b_acc / div);

            int x_left = x - radius;
            int x_right = x + radius + 1;
            int p_left = x_left < 0 ? 0 : (x_left >= width ? width - 1 : x_left);
            int p_right = x_right < 0 ? 0 : (x_right >= width ? width - 1 : x_right);

            r_acc += src[row_idx + p_right * 3 + 0] - src[row_idx + p_left * 3 + 0];
            g_acc += src[row_idx + p_right * 3 + 1] - src[row_idx + p_left * 3 + 1];
            b_acc += src[row_idx + p_right * 3 + 2] - src[row_idx + p_left * 3 + 2];
        }
    }

    // Vertical pass
    for (int x = 0; x < width; ++x) {
        int r_acc = 0, g_acc = 0, b_acc = 0;

        for (int i = -radius; i <= radius; ++i) {
            int py = i < 0 ? 0 : (i >= height ? height - 1 : i);
            r_acc += temp[py * width * 3 + x * 3 + 0];
            g_acc += temp[py * width * 3 + x * 3 + 1];
            b_acc += temp[py * width * 3 + x * 3 + 2];
        }

        for (int y = 0; y < height; ++y) {
            dst[y * width * 3 + x * 3 + 0] = (uint8_t)(r_acc / div);
            dst[y * width * 3 + x * 3 + 1] = (uint8_t)(g_acc / div);
            dst[y * width * 3 + x * 3 + 2] = (uint8_t)(b_acc / div);

            int y_top = y - radius;
            int y_bot = y + radius + 1;
            int p_top = y_top < 0 ? 0 : (y_top >= height ? height - 1 : y_top);
            int p_bot = y_bot < 0 ? 0 : (y_bot >= height ? height - 1 : y_bot);

            r_acc += temp[p_bot * width * 3 + x * 3 + 0] - temp[p_top * width * 3 + x * 3 + 0];
            g_acc += temp[p_bot * width * 3 + x * 3 + 1] - temp[p_top * width * 3 + x * 3 + 1];
            b_acc += temp[p_bot * width * 3 + x * 3 + 2] - temp[p_top * width * 3 + x * 3 + 2];
        }
    }

    free(temp);
}
