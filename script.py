from argparse import ArgumentParser, Namespace
import re


BASE_URL = 'https://www.ozon.ru/'

# Инициализация парсера аргументов командной строки
def init_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description='Парсинг Ozon')

    # Оба аргумента позиционные. Сначала поисковой запрос, потом артикул товара
    parser.add_argument('query', help='Поисковой запрос')
    parser.add_argument('article', help='Артикул товара')

    return parser


# Проверка аргументов на правильность
def check_arguments(args: Namespace) -> tuple[str | None, str | None, str | None]:
    try:
        # Если одного из аргументов нет, возвращаю ошибку
        query, article = args.query, args.article
    except Exception as ex:
        return None, None, f'Ошибка в извлечении значений аргументов скрипта - {ex.args}'

    # Проверка аргумента query на правильность
    # Если в поисковом запросе есть только пробелы, возвращаю ошибку, такой запрос не имеет смысла
    if len(query.strip()) == 0:
        return None, None, 'Поисковый запрос составлен неверно, в нём должен быть хотя бы один непробельный символ'

    # Проверка аргумента article на правильность. Артикул состоит из 10 чисел
    # Решил использовать регулярное выражение, чтобы не делать сложные условия
    if not re.match(r'^[0-9]{10}$', article):
        return None, None, 'Введённый артикул неверный, он должен состоять из 10 числовых символов'

    # Если всё правильно, возвращаем query и article без ошибок
    return query, article, None


# Общая функция для поиска товара
def find_product(query: str, article: str) -> tuple[dict | str, str | None]:
    pass


if __name__ == '__main__':
    parser = init_arg_parser()

    # Чтение аргументов
    try:
        args = parser.parse_args()
    except Exception as ex:
        print(f'Ошибка в получении аргументов скрипта: {ex.__str__()}')
        exit()

    query, article, error = check_arguments(args)
    if error is not None:
        print(error)
        exit()

    print(query, article)
