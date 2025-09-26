def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key

numbers = [5, 3, 8, 4, 2]
insertion_sort(numbers)
print("Відсортований список:", numbers)
