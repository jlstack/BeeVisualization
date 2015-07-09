__author__ = 'lukestack'
import os
import shutil


def main(input_dir, output_dir, time):
    if not input_dir.endswith("/"):
        input_dir += "/"
    if not output_dir.endswith("/"):
        output_dir += "/"
    if "pit1" in input_dir:
        output_dir = output_dir + time + "/pit1/"
    else:
        output_dir = output_dir + time + "/pit2/"
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    directories = os.listdir(input_dir)
    directories.sort()
    for d in directories:
        if os.path.isdir(input_dir + d + "/audio/"):
            audio_dir = input_dir + d + "/audio/"
            date = d.split("-")
            date.reverse()
            date = "-".join(date)
            if "Org" in date:
                index = date.index("Org")
                date = date[:index] + date[index + 3:]
            recordings = os.listdir(audio_dir)
            recordings.sort()
            for rec in recordings:
                for i in range(0, 3):
                    t = time + ":0" + str(i) + ":"
                    if t in rec:
                        shutil.copyfile(audio_dir + rec, output_dir + date + '_' + rec)


if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2], sys.argv[3])