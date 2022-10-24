import random
from gost import ecb
from utils import module_degree, module_inversion
import sys

CONSTANT_P = 31481
CONSTANT_Q = 787
CONSTANT_A = 1928
CONSTANT_X = 2


def find_v(r: int, s: int, h: int) -> int:
    y = module_degree(CONSTANT_A, CONSTANT_X, CONSTANT_P)
    u_1 = module_degree(module_inversion(h, CONSTANT_Q), 1, CONSTANT_Q, s)
    u_2 = module_degree(module_inversion(h, CONSTANT_Q), 1, CONSTANT_Q, -r)
    return module_degree(module_degree(CONSTANT_A, u_1, CONSTANT_P, y ** u_2), 1, CONSTANT_Q)


def hash_calc(message: str) -> int:
    # Пока нерабочая функция, должна возвращать хэш файла

    key8 = "00000000"
    h = ecb(key8, message, True)
    return h


def get_sign(file_path: str, hash_summ: int):
    """
    Получает рандомное k 0 < k < q
    Вычисляет r,s на основе k
    Если r или s == 0 вычисление k происходит снова
    Вычесленная подпись (r, s) записывается в filename.sign
    """
    k_rand: int = random.randint(1, CONSTANT_Q - 1)
    r: int = module_degree(module_degree(CONSTANT_A, k_rand, CONSTANT_P), 1, CONSTANT_Q)
    s: int = module_degree((k_rand * hash_summ + CONSTANT_X * r), 1, CONSTANT_Q)
    if r == 0 or s == 0:
        get_sign(file_path, hash_summ)
    sign: tuple = (r, s)
    new_file_name = f"{file_path}.sign"
    try:
        with open(new_file_name, "wb") as fh:
            for item in sign:
                bt = (str(item) + '\n').encode()
                fh.write(bt)
    except:
        raise ValueError("Ошибка при создании подписи")
    else:
        print(f"Создана подпись для файла {file_path}: {new_file_name}")


def check_sign(file_path: str, hash_summ: int):
    sign_filename: str = f"{file_path}.sign"
    sign = ()
    try:
        with open(sign_filename, "rb") as rb:
            for line in rb:
                s = line
                s = int(s[:-1])
                sign = sign + (s,)
    except:
        raise ValueError(f"Подписи дла {file_path} не найдено")
    if not 0 < sign[0] < CONSTANT_Q or not 0 < sign[1] < CONSTANT_Q:
        print("Подпись не действительна")
        return
    if find_v(sign[0], sign[1], hash_summ) != sign[0]:
        print("Подпись не действительна")
        return
    print(f"Подпись {file_path} действительна")


def main(file_path: str, mode: str):
    if not file_path:
        raise ValueError("Не указан путь к файлу с сообщением")
    with open(file_path, "rb") as rb:
        data = rb.read()
    hash_summ: int = hash_calc(data)

    match mode:
        case "get":
            get_sign(file_path, hash_summ)
        case "check":
            check_sign(file_path, hash_summ)


if __name__ == '__main__':
    # main(sys.argv[1])
    main("hello.txt", "get")
    main("hello.txt", "check")

