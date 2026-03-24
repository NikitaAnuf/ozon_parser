from argparse import ArgumentParser, Namespace
import re
import time
import random
from datetime import datetime
from pprint import pprint

# Парсер на основе Chrome
from undetected_chromedriver import Chrome
from fake_useragent import UserAgent

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


BASE_URL = 'https://www.ozon.ru/'
# Стандартная пауза для имитирования человека
MIMIC_PAUSE = 1 # sec
# Стандартная пауза для ожидания появления элемента
DRIVER_PATIENCE = 10 # sec
# Placeholder в поисковой строке. Вынесен в отдельную переменную для возможности быстрой замены
SEARCH_INPUT_PLACEHOLDER = 'Искать на Ozon'
# Название класса секции карточек товаров
SECTION_CLASS_NAME = 'qi0_24'
# Класс, определяющий карточки товара
CARD_CLASS_NAME = 'tile-root'
# Количество просматриваемых карточек
CARD_SEARCH_PATIENCE = 100
# Атрибут ссылки на карточку, в котором нужно искать артикул
SKU_TAG_ATTRIBUTE = 'data-prerender'
# Время ожидания подгрузки страницы
SCROLL_LOAD_PATIENCE = 5 # sec


# Инициализация парсера аргументов командной строки
def init_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description='Парсинг Ozon')

    # Оба аргумента позиционные. Сначала поисковой запрос, потом артикул товара
    parser.add_argument('query', help='Поисковой запрос')
    parser.add_argument('sku', help='Артикул товара')

    return parser


# Проверка аргументов на правильность
def check_arguments(args: Namespace) -> tuple[str | None, str | None, str | None]:
    try:
        # Если одного из аргументов нет, возвращаю ошибку
        query, sku = args.query, args.sku
    except Exception as ex:
        return None, None, f'Ошибка в извлечении значений аргументов скрипта - {ex.args}'

    # Проверка аргумента query на правильность
    # Если в поисковом запросе есть только пробелы, возвращаю ошибку, такой запрос не имеет смысла
    if len(query.strip()) == 0:
        return None, None, 'Поисковый запрос составлен неверно, в нём должен быть хотя бы один непробельный символ'

    # Проверка аргумента sku на правильность
    if not re.match(r'^[0-9]+$', sku):
        return None, None, 'Введённый артикул неверный, он должен состоять только из числовых символов'

    # Если всё правильно, возвращаем query и sku без ошибок
    return query, sku, None


def init_web_driver() -> Chrome:
    ua = UserAgent()
    # Рандомный user agent. Нужен, чтобы парсер было сложнее вычислить
    user_agent = ua.random

    options = Options()

    # options.add_argument('--headless')
    options.add_argument('--disable-gpu') # Отключаю GPU для стабильности работы
    options.add_argument('--window-size=1920,1080') # Стандартный размер окна, чтобы вёрстка не изменялась
    options.add_argument(f'user-agent={user_agent}')

    # При закрытии драйвера в логах возвращалась проигнорированная ошибка дескриптора
    # Параметр enable_cdp_events в драйвере позволяет её предотвратить
    driver = Chrome(options=options, enable_cdp_events=True)

    return driver


# Поиск товаров по тексту запроса
def input_search_query(driver: Chrome, query: str) -> str | None:
    try:
        # Ждём пока появится строка поиска
        input = WebDriverWait(driver, DRIVER_PATIENCE).until(
            expected_conditions.element_to_be_clickable((By.XPATH, f'//input[@placeholder="{SEARCH_INPUT_PLACEHOLDER}"]'))
        )
        time.sleep(MIMIC_PAUSE)
    except Exception as ex:
        return f'Поисковая строка не была найдена = {ex.__str__()}'

    try:
        input.clear()

        # Посылаю буквы по одной со случайной паузой, имитирую действия человека
        for char in query:
            input.send_keys(char)
            time.sleep(random.uniform(.05, .2))

        # После ввода запроса отправляю нажатие на Enter
        input.send_keys(Keys.RETURN)
    except Exception as ex:
        return f'Не удалось ввести запрос в поисковую строку = {ex.__str__()}'

    return None


def crawl_through_page(driver: Chrome, target_sku: str) -> tuple[bool | None, int | None, int | None, str | None]:
    def get_all_cards() -> list:
        cards = driver.find_elements(By.CLASS_NAME, f'{CARD_CLASS_NAME}')
        if cards:
            return cards
        return []

    def extract_sku_from_card(card) -> str | None:
        try:
            link_elem = card.find_element(By.XPATH, ".//a[contains(@href, '/product/')]")
            href = link_elem.get_attribute("href")
            if href:
                match = re.search(r'/product/[^/]*?(\d{5,50})[/?]', href)
                if match:
                    return match.group(1)
        except:
            pass
        return None

    scroll_count = 0
    no_new_cards_counter = 0
    unique_skus = []
    last_unique_skus_len = -1

    while len(unique_skus) <= CARD_SEARCH_PATIENCE:
        cards = get_all_cards()
        if not cards:
            try:
                # Ждём появления хотя бы одной карточки
                WebDriverWait(driver, DRIVER_PATIENCE).until(
                    expected_conditions.presence_of_element_located((By.XPATH, f'.//*[contains(@class, {CARD_CLASS_NAME})]'))
                )
                cards = get_all_cards()
            except TimeoutException:
                return False, None, None, "Не найдены карточки товаров"
            if not cards:
                return False, None, None, "Не найдены карточки товаров"

        if last_unique_skus_len < len(unique_skus):
            last_unique_skus_len = len(unique_skus)
            for i in range(len(cards)):
                try:
                    sku = extract_sku_from_card(cards[i])
                    if sku in unique_skus:
                        continue
                    else:
                        unique_skus.append(sku)
                except StaleElementReferenceException:
                    continue
                if sku and sku == target_sku:
                    return True, len(unique_skus), scroll_count + 1, None
                if len(unique_skus) > CARD_SEARCH_PATIENCE:
                    break
            no_new_cards_counter = 0
        else:
            no_new_cards_counter += 1
            if no_new_cards_counter >= 5:
                break

        if len(unique_skus) > CARD_SEARCH_PATIENCE:
            break

        # Скролл до последней известной карточки
        driver.execute_script("arguments[0].scrollIntoView();", cards[-1])
        scroll_count += 1
        time.sleep(MIMIC_PAUSE)

        try:
            WebDriverWait(driver, SCROLL_LOAD_PATIENCE).until(
                lambda d: len(get_all_cards()) >= 48
            )
        except TimeoutException:
            pass

        time.sleep(MIMIC_PAUSE)

    return False, None, None, None


def compile_result(query: str, sku: str, position: int, page: int) -> dict:
    return {
        'query': query,
        'sku': sku,
        'position': position,
        'page': page,
        'total_checked': CARD_SEARCH_PATIENCE,
        'timestamp': datetime.now().isoformat(timespec='seconds')
    }


# Общая функция для поиска товара
def find_product(query: str, sku: str) -> tuple[dict | str | None, str | None]:
    driver = None
    try:
        try:
            driver = init_web_driver()
        except Exception as ex:
            return None, f'Ошибка в инициализации веб-драйвера - {ex.__str__()}'

        # Открытие главной страницы
        driver.get(BASE_URL)
        # Ожидание проверки антибот защиты
        time.sleep(MIMIC_PAUSE)

        error = input_search_query(driver, query)
        time.sleep(MIMIC_PAUSE)
        if error is not None:
            return None, error

        is_found, position, page, error = crawl_through_page(driver, sku)
    finally:
        time.sleep(MIMIC_PAUSE)
        if driver:
            driver.quit()

    if error is not None:
        return None, error
    elif not is_found:
        return 'not_found', None
    else:
        return compile_result(query, sku, position, page), None



if __name__ == '__main__':
    parser = init_arg_parser()

    # Чтение аргументов
    try:
        args = parser.parse_args()
    except Exception as ex:
        print(f'Ошибка в получении аргументов скрипта: {ex.__str__()}')
        exit()

    query, sku, error = check_arguments(args)
    if error is not None:
        print(error)
        exit()

    result, error = find_product(query, sku)
    if error is not None:
        print(error)
    else:
        pprint(result, sort_dicts=False)
