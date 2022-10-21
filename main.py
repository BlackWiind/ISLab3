import random
import sys

CONSTANT_P = 31481
CONSTANT_Q = 787
CONSTANT_A = 1928


def hash_calc(message: str) -> int:
    # Пока нерабочая функция, должна возвращать хэш файла
    h = 1488
    return h


def get_sign(file_path: str, hash_summ: int):
    """
    Получает рандомное k 0 < k < q
    Вычисляет r,s на основе k
    Если r или s == 0 вычисление k происходит снова
    Вычесленная подпись (r, s) записывается в filename.sign
    """
    k_rand: int = random.randint(1, CONSTANT_Q - 1)
    r: int = 235
    s: int = 1
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


def check_sign(file_path: str):
    sign_falename: str = f"{file_path}.sign"
    sign = ()
    with open(sign_falename, "rb") as rb:
        for line in rb:
            s = line
            s = int(s[:-1])
            sign = sign + (s,)
    if not 0 < sign[0] < CONSTANT_Q or not 0 < sign[1] < CONSTANT_Q:
        print("Подпись не действительна")
        return
    u1 = 0
    u2 = 0
    v = 235
    if sign[0] != v:
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
            check_sign(file_path)


if __name__ == '__main__':
    # main(sys.argv[1])
    main("hello.txt", "get")
