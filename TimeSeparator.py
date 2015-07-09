__author__ = 'lukestack'
import os
import shutil

times = ['00', '05', '08', '12', '15', '17', '20']


def main(input_dir, output_dir):
    if not input_dir.endswith("/"):
        input_dir += "/"
    if not output_dir.endswith("/"):
        output_dir += "/"
    for time in times:
        if "pit1" in input_dir:
            pit_output_dir = output_dir + "/pit1/"
            time_output_dir = output_dir + "/pit1/" + time + "/"
        else:
            pit_output_dir = output_dir + "/pit2/"
            time_output_dir = output_dir + "/pit2/" + time + "/"
        if not os.path.isdir(time_output_dir):
            os.makedirs(time_output_dir)

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
                for time in times:
                    for i in range(0, 3):
                        t = time + ":0" + str(i) + ":"
                        if t in rec:
                            print time_output_dir + date + '_' + rec
                            shutil.copyfile(audio_dir + rec, pit_output_dir + time + '/' + date + '_' + rec)


if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2])