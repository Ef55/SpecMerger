# << 0.1 Introduction >> TITLE
# << This is the introduction of the specification >>
# << - This specification may not be used in any way outside of this project >>
# << - This specification is purely invented >>

# << 1.0 Notation >> TITLE
# << I misread the description whoops >>
# << - double denotes a floating-point value >>
double = float
# << - string denotes a text value >>
string = str
# << - number denotes an integer value >>
number = int


# << 1.1 int_mul >> TITLE
# << x:number, y:number >> INPUTS
def int_mul(x: number, y: number):
    # << This function is used to multiply two integers. >>
    # << 1. Let z = x + y >>
    z = x + y
    # << 2. Let res = (z^2 - x^2 - y^2)/2 >>
    res = (z**2 - x**2 - y**2) >> 1
    # << 4. Return res. >>
    return res

# << 1.2 string_concat >> TITLE
# << s1:string, s2:string, i:number >> INPUTS
def string_concat(s1: string, s2: string, i:number):
    # << This function is used to concatenate two strings. >>
    # << 1. Let s3 be the copy of s1. >>
    s3 = s1
    # << 2. For each character c in s2 >>
    for c in s2:
        # << 2a. Let s3 = s3 + c >>
        s3 += c
    # << 3. Return s3. >>
    return s3

# << 2.0 complex_useless_maths >> TITLE
# << x:number, y:number, s:string, w:number, ctr:number >> INPUTS
def complex_useless_maths(x:number,y:number,s:string,w:number,ctr:number):
    # << 1. Let l be the length of s >>
    l = len(s)
    # << 2. Let z = (x + y)^2 >>
    z = (x + y)**2
    # << 3. >> WILDCARD
    # << 3a. >> WILDCARD
    # This is because this is just doing the operation z mod l which is way easier to implement, since z and l are > 0
    z = z % l
    # << 4. Return int_mul(z,ctr) + w >>
    return int_mul(z, ctr) + w
