HW = "Hello World"


def main():
    try:
        temp = ""
    except Exception as e:
        print(e)
    start = input("Please enter start number: ")
    end = input("Please enter end number: ")
    step = input("Please enter step number: ")
    for attempt in range(int(start), int(end), int(step)):
        print(f"Attempt #{attempt}")
    pass

    pass

    return temp


if __name__ == "__main__":
    main()
