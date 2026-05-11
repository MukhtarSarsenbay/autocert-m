from subprocess import call


def convert_to(path):
	#subprocess.run(['unoconv', '-f', 'pdf', path],  shell=True)
	call(["unoconv","-f","pdf",path])
	#call(["libreoffice","--headless","--convert-to", "pdf", "~"+str(path)])
	

