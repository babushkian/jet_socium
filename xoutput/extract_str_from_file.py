import sys, os

def get_extr(string, suf):
	to_replace=["\\", "/", "^", "&", ":", ";"]
	suf_conv=""
	for st in suf:
		if st in to_replace:
			suf_conv = suf_conv + "_"
		else:
			suf_conv = suf_conv + st
	
	a=string.split(".")
	print(a)
	b="".join(a[:-1])

	print(suf_conv)
	return b + "_" + suf_conv[:8]+"."+a[-1]


arg=sys.argv
print(arg)
file = sys.argv[1]
ext_str = sys.argv[2].lower()

extr=get_extr(file, ext_str)

f_from=open(file,"r", encoding="utf-16")
f_to=open(extr, "w",encoding="utf-16")

while True:
	string=f_from.readline()
	string1=string.lower()
	if string =="": break
	if string1.find(ext_str)>-1:
#		print(string)
		f_to.write(string)
f_from.close()
f_to.close()
