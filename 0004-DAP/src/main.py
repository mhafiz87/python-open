HW = "Hello World"


def main():
    start = input("Please enter start number: ")
    end = input("Please enter end number: ")
    step = input("Please enter step number: ")
    for attempt in range(int(start), int(end), int(step)):
        print(f"Attempt #{attempt}")
    pass


if __name__ == "__main__":
    main()
