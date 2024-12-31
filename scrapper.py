from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep


def scrapeRestaurant(url):
    options = Options()
    options.add_argument("--headless")  # Run in headless mode for lower resource usage
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-images")  # Disable loading images
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")  # Disable audio
    options.add_argument("--disable-plugins")  # Disable plugins
    options.add_argument("--no-sandbox")  # Improve performance
    options.add_argument("--disable-dev-shm-usage")  # Avoid shared memory issues
    options.add_argument("--window-size=1920,1080")  # Ensure a large viewport
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")


    # Set preferences for blocking other resource types
    prefs = {
        "profile.managed_default_content_settings.images": 2,  # Block images
        "profile.default_content_setting_values.media_stream": 2,  # Block video streams
        "profile.default_content_setting_values.geolocation": 2,  # Block location access
        "profile.default_content_setting_values.notifications": 2,  # Block notifications
    }
    options.add_experimental_option("prefs", prefs)

    # Initialize the WebDriver
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=options
    )
    driver.get(url)

    reviews = []
    counter = 1
    running = True
    retries = 0

    while running:
        try:
            # Wait for all elements to be present in DOM
            WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "afkKaa-4T28-")))

            # Get reviews
            reviewsTag = driver.find_elements(By.CLASS_NAME, "afkKaa-4T28-")
            for review in reviewsTag:
                try:
                    # Extract ratings
                    ratingsTag = review.find_elements(By.CSS_SELECTOR, ".-k5xpTfSXac-")
                    reviewsRating = []
                    for r in ratingsTag:
                        words = r.text.split()
                        if len(words) >= 2:
                            ratingsDict = {words[0]: words[1]}
                            reviewsRating.append(ratingsDict)

                    # Extract review date and text
                    reviewDate = review.find_element(By.CSS_SELECTOR, ".iLkEeQbexGs-").text
                    reviewText = review.find_element(By.CSS_SELECTOR, ".l9bbXUdC9v0-").text.replace('\n', '')

                    # Store reviews in a structured format
                    ratingsTotal = {"review_" + str(counter): {"Ratings": reviewsRating, "Date": reviewDate, "Review": reviewText}}
                    reviews.append(ratingsTotal)
                    # retries = 0
                    counter += 1

                except NoSuchElementException:
                    print("Element not found! Skipping...")
                    continue
                except StaleElementReferenceException:
                    print("Stale element reference. Skipping...")
                    continue

            # Navigate to the next page
            max_retries = 3
            for _ in range(max_retries):
                try:
                    next_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[aria-label='Go to the next page']"))
                    )
                    if next_button.is_displayed():
                        next_button.click()
                        print(f"Navigating to the next page, collected {len(reviews)} reviews so far.")
                        break
                except NoSuchElementException:
                    print("Next button not found. Exiting scraping.")
                    running = False
                    break
                except StaleElementReferenceException:
                    print("Stale element reference for next button. Retrying...")
                    sleep(2)
            else:
                print("Failed to click next button after retries. Exiting loop.")
                running = False

        except TimeoutException:
            print("Timeout exception occurred, Refreshing page...")
            print("Retries: ",retries)
            retries += 1
            if retries >= 3:
                print("End of reviews reached after retries. Exiting script.")
                running = False
            else:
                driver.refresh()

        except NoSuchElementException:
            print("No more reviews to scrape. Exiting.")
            running = False

    driver.quit()

    return reviews