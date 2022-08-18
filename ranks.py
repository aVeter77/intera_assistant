def get_sum_text(sum):
    """Разделение суммы на разряды"""

    point = sum.find('.')
    if point > 0:
        reverse_sum = sum[0:point][::-1]
    else:
        reverse_sum = sum[::-1]

    rank_sum = []
    start = 0
    if len(sum) > 3:
        for rank in range(3, len(sum), 3):
            rank_sum.append(reverse_sum[start:rank])
            start = rank
    rank_sum.append(reverse_sum[start: len(sum)])
    reverse_sum = ' '.join(rank_sum)

    if point > 0:
        return reverse_sum[::-1] + sum[point:]

    return reverse_sum[::-1]
