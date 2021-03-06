# -*- coding: utf-8 -*-

""" httperf-plot

.. moduleauthor:: limseok <gtolarc@gmail.com>
"""

import argparse
import re
import subprocess
import csv
import time

from plot import Canvas


def parse_args():
    parser = argparse.ArgumentParser(description='httperf-plot is a python wrapper around httperf')

    parser.add_argument('--server', metavar='S',
                        dest='--server', action='store',
                        help='specifies the IP hostname S of the server')
    parser.add_argument('--port', metavar='N',
                        dest='--port', action='store',
                        help='specifies the port number N on which the web server is listening for HTTP requests')
    parser.add_argument('--uri', metavar='S',
                        dest='--uri', action='store',
                        help='specifies that URI S should be accessed on the server')
    parser.add_argument('--timeout', metavar='X',
                        dest='--timeout', action='store',
                        help='specifies the amount of time X that httperf is willing to wait for a server reaction')
    parser.add_argument('--rate', metavar='X',
                        dest='--rate', action='store',
                        help='specifies the fixed rate X at which connections or sessions are created')
    parser.add_argument('--num-conns', metavar='N',
                        dest='--num-conns', action='store',
                        help='specifies the total number of connections N to create')
    parser.add_argument('--num-calls', metavar='N',
                        dest='--num-calls', action='store',
                        help='specifies the total number of calls N to issue on each connection before closing it')
    parser.add_argument('--method', metavar='S',
                        dest='--method', action='store',
                        help='specifies the method S that should be used when issuing an HTTP request')
    parser.add_argument('--add-header', metavar='S',
                        dest='--add-header', action='store',
                        help='specifies to include string S as an additional request header')
    parser.add_argument('--wsesslog', metavar='N,X,F',
                        dest='--wsesslog', action='store',
                        help='specifies the following parameters: N is the number of sessions to initiate, '
                             'X is the user think-time (in seconds) that separates consecutive call bursts, '
                             'and many aspects of user sessions can be specified in an input file F')
    parser.add_argument('--hog',
                        dest='--hog', action='store_true', default=False,
                        help='specifies the hog parameter')
    parser.add_argument('--verbose',
                        dest='--verbose', action='store_true', default=False,
                        help='specifies the verbose parameter')

    parser.add_argument('--ramp-up', metavar='X,N',
                        dest='--ramp-up', action='store',
                        help='specifies the ramp-up rate X, times N (httperf-plot parameter)')
    parser.add_argument('--csv', metavar='S',
                        dest='--csv', action='store',
                        help='specifies the csv output file')
    parser.add_argument('--plot',
                        dest='--plot', action='store_true', default=False,
                        help='specifies to plot csv file')

    return vars(parser.parse_args())


def httperf_once(args):
    rst = {}

    params = []
    for arg in args.items():
        if isinstance(arg[1], bool) and arg[1]:
            params += [arg[0]]
        elif arg[1] is not None:
            params += ['='.join(arg)]
    # out_bytes = subprocess.check_output(['httperf'] + ['='.join(arg) for arg in args.items() if arg[1] is not None])
    out_bytes = subprocess.check_output(['httperf'] + params)
    out_bytes_str = out_bytes.decode()
    print(out_bytes_str)

    rst['Number of requests'] = int(re.findall(r'(Total: connections \d+ requests )(\d+)', out_bytes_str)[0][1])
    rst['Rate'] = int(args['--rate'])
    rst['Request rate'] = float(re.findall(r'(Request rate: )(\d+\.\d+)', out_bytes_str)[0][1])
    rst['Response time'] = float(re.findall(r'(Reply time \[ms\]: response )(\d+\.\d+)', out_bytes_str)[0][1])
    rst['Response status 1xx'] = int(re.findall(r'(1xx=)(\d+)', out_bytes_str)[0][1])
    rst['Response status 2xx'] = int(re.findall(r'(2xx=)(\d+)', out_bytes_str)[0][1])
    rst['Response status 3xx'] = int(re.findall(r'(3xx=)(\d+)', out_bytes_str)[0][1])
    rst['Response status 4xx'] = int(re.findall(r'(4xx=)(\d+)', out_bytes_str)[0][1])
    rst['Response status 5xx'] = int(re.findall(r'(5xx=)(\d+)', out_bytes_str)[0][1])

    rr_perc = re.findall(r'(Percentages of the replies served at a given rate:)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)', out_bytes_str)
    if len(rr_perc) > 0:
        for k, v in {x[0]: x[1] for x in [rr_perc[0][j].split(': ') for j in range(2, len(rr_perc[0]), 2)]}.iteritems():
            rst['Response rate ' + k] = float(v)

    rt_perc = re.findall(r'(Percentages of the requests served within a certain time \(ms\) :)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)'
                         r'(\s+)(\d+%: \d+)', out_bytes_str)
    if len(rt_perc) > 0:
        for k, v in {x[0]: x[1] for x in [rt_perc[0][j].split(': ') for j in range(2, len(rt_perc[0]), 2)]}.iteritems():
            rst['Response time ' + k] = float(v)

    return rst


def httperf_plot(data):
    parse_data = [(float(datum['Rate']), float(datum['Request rate'])) for datum in data]
    a = Canvas(title='Rate - Request rate', xlab='Rate', ylab='Request rate',
               xrange=(min([float(datum['Rate']) for datum in data]), max([float(datum['Rate']) for datum in data])),
               yrange=(min([float(datum['Request rate']) for datum in data]) - 5,
                       max([float(datum['Request rate']) for datum in data]) + 5))
    a.plot(parse_data).save('plot1.png')

    parse_data = [(float(datum['Rate']), float(datum['Response time'])) for datum in data]
    b = Canvas(title='Rate - Response time', xlab='Rate', ylab='Response time',
               xrange=(min([float(datum['Rate']) for datum in data]), max([float(datum['Rate']) for datum in data])),
               yrange=(min([float(datum['Response time']) for datum in data]) - 5,
                       max([float(datum['Response time']) for datum in data]) + 5))
    b.plot(parse_data).save('plot2.png')

    parse_data = [(float(datum['Rate']),
                   (float(datum['Response status 2xx']) + float(datum['Response status 3xx'])) / float(datum['Number of requests']) * 100.0)
                  for datum in data]
    c = Canvas(title='Rate - Success rate', xlab='Rate', ylab='Success rate',
               xrange=(min([float(datum['Rate']) for datum in data]), max([float(datum['Rate']) for datum in data])),
               yrange=(0 - 5, 100 + 5))
    c.plot(parse_data).save('plot3.png')

    Canvas.show()


# def httperf_TIME_WAIT():
#     out_bytes = subprocess.check_output(r"""netstat -t | wc -l""", shell=True)
#     out_bytes_str = out_bytes.decode()
#     return int(out_bytes_str)


if __name__ == '__main__':
    args = parse_args()
    plot_data = []

    csv_file = ''
    if args['--csv'] is not None:
        csv_file = args['--csv']
        args['--csv'] = None

    plot = args['--plot']
    args['--plot'] = None

    if not args['--hog']:
        args['--hog'] = None

    if not args['--verbose']:
        args['--verbose'] = None

    if plot:
        if csv_file:
            plot_data = []
            with open(csv_file, 'r') as csv_fd:
                reader = csv.DictReader(csv_fd)
                for row in reader:
                    plot_data.append(row)

            httperf_plot(plot_data)
        else:
            exit(1)
    elif args['--ramp-up'] is not None:
        ramp_up = args['--ramp-up'].split(',')
        del args['--ramp-up']

        if csv_file:
            for i in range(int(ramp_up[1])):
                plot_data.append(httperf_once(args))
                args['--rate'] = str(int(args['--rate']) + int(ramp_up[0]))

            if len(plot_data) > 0:
                with open(csv_file, 'w') as csv_fd:
                    field_names = plot_data[0].keys()
                    writer = csv.DictWriter(csv_fd, fieldnames=field_names)

                    writer.writeheader()
                    for row in plot_data:
                        writer.writerow(row)
        else:
            for i in range(int(ramp_up[1])):
                plot_data.append(httperf_once(args))
                args['--rate'] = str(int(args['--rate']) + int(ramp_up[0]))

            httperf_plot(plot_data)
    else:
        httperf_once(args)
