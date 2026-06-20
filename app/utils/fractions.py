from fractions import Fraction

def to_fraction(value):
    try:
        return Fraction(str(value))
    except:
        return Fraction(0)