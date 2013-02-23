def cleanget(dictionary, key):
    val = {}
    if key in dictionary:
        val = dictionary.get(key)
    return val


