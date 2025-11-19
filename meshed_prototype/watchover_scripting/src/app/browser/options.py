from functools import lru_cache


from pydoll.browser.options import ChromiumOptions


@lru_cache(typed=True, maxsize=1)
def get_brower_options() -> ChromiumOptions:
    options = ChromiumOptions()

    options.headless = True

    # Core stealth
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")

    # Faster scrapping
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-features=NetworkPrediction")
    options.add_argument("--dns-prefetch-disable")

    # User agent
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    )

    # Language and locale
    options.add_argument("--lang=vi-VN")
    options.add_argument("--accept-lang=vi-VN,vi;q=0.9")
    options.add_argument("--tz=Asia/Ho_Chi_Minh")

    # WebGL (software renderer to avoid unique GPU signatures)
    options.add_argument("--use-gl=swiftshader")
    options.add_argument("--disable-features=WebGLDraftExtensions")

    # WebRTC IP leak prevention
    options.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")

    # Window size (common resolution)
    options.add_argument("--window-size=1920,1080")

    # Privacy
    options.add_argument("--disable-features=Translate")
    options.add_argument("--disable-sync")
    options.add_argument("--incognito")

    return options
