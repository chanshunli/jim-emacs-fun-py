import sys
sys.path.append("/Users/emacspy/EmacsPyPro/jim-emacs-fun-py")

import algo

def test_min():
    values = (2, 3, 1, 4, 6)

    val = algo.min(values)
    assert val == 1

def test_max():
    values = (2, 3, 1, 4, 6)

    val = algo.max(values)
    assert val == 6

