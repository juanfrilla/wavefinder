from front import *

if __name__ == "__main__":
    if is_playwright_installed():
        print("Playwright is already installed.")
    else:
        print("Playwright is not installed. Installing...")
        install_playwright()

    urls = [
        "https://www.windguru.cz/49326",  # Jameos del agua
        "https://www.windguru.cz/49325",  # La garita
        "https://www.windguru.cz/49328",  # famara
        "https://www.windguru.cz/586104",  # costa teguise
    ]

    # df = multithread.scrape_multiple_requests(urls, Windguru())

    # df = final_format(df)
    # print()
    plot_data(urls)
