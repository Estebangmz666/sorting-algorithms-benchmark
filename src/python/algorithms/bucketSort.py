def bucketSort(array):
    minValue = 10_000_000
    rangeSize = 90_000_000
    bucketCount = 4096
    buckets = [[] for _ in range(bucketCount)]

    for value in array:
        index = (value - minValue) * bucketCount // rangeSize
        buckets[index].append(value)

    position = 0
    for bucket in buckets:
        for i in range(1, len(bucket)):
            key = bucket[i]
            j = i
            while j > 0 and bucket[j - 1] > key:
                bucket[j] = bucket[j - 1]
                j -= 1
            bucket[j] = key
        for value in bucket:
            array[position] = value
            position += 1
