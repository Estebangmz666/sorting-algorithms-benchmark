def dualPivotQuickSort(array):
    if len(array) < 2:
        return
    pending = [(0, len(array) - 1)]

    while pending:
        left, right = pending.pop()
        if left >= right:
            continue

        if array[left] > array[right]:
            array[left], array[right] = array[right], array[left]
        leftPivot = array[left]
        rightPivot = array[right]
        less = left + 1
        greater = right - 1
        current = less

        while current <= greater:
            if array[current] < leftPivot:
                array[current], array[less] = array[less], array[current]
                less += 1
            elif array[current] > rightPivot:
                while current < greater and array[greater] > rightPivot:
                    greater -= 1
                array[current], array[greater] = array[greater], array[current]
                greater -= 1
                if array[current] < leftPivot:
                    array[current], array[less] = array[less], array[current]
                    less += 1
            current += 1

        less -= 1
        greater += 1
        array[left], array[less] = array[less], array[left]
        array[right], array[greater] = array[greater], array[right]

        if left < less - 1:
            pending.append((left, less - 1))
        if leftPivot < rightPivot and less + 1 < greater - 1:
            pending.append((less + 1, greater - 1))
        if greater + 1 < right:
            pending.append((greater + 1, right))
