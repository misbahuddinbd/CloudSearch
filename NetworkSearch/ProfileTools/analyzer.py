#!/usr/bin/python
""" A profile stats analyzer.

A module contains a class used for
analyze the collected statistics
and then produce graphs.

Note install matplot "sudo apt-get install python-matplotlib"

@author: Misbah Uddin
"""

import argparse
import numpy
import matplotlib.pyplot as plt
import matplotlib
from glob import glob
import os


def get_args():
    """ A function for getting command line arguments."""

    parser = argparse.ArgumentParser(description="A profile stats analyzer")
    parser.add_argument("-global_lat", action='store_true', default=False,
                        help='analyze and plot a graph of global latency')
    parser.add_argument("-resource", action='store_true', default=False,
                        help='analyze and plot a graph of global CPU and \
                        Memory resouces')
    parser.add_argument("-detail", action='store_true', default=False,
                        help='analyze and plot a graph of detail latency')
    parser.add_argument("-compare", action='store_true', default=False,
                        help='compare 90% loaded cloud and normal cloud')
    parser.add_argument("path", type=str,
                        help='directory path to the statistics')
    return parser.parse_args()


class Analyzer(object):
    """ A class for analyzing the collected statistics
    and then produce graphs."""

    def __init__(self, args):
        self.args = args

    def run_special__for_model(self):
        pass

    def run_global_latency(self):
        ############################
        # read and manipulate data #
        ############################
        read_option = {'dtype': float, 'delimiter': ',', 'skip_header': 1}
        data = self._read_all_information('global/', 'stats*.log', read_option)

        #############################
        # manipulate data for graph #
        #############################
        self._plot_mean_global(data,)
        self._plot_boxplot_global(
                data[2], 2,
                [10, 20, 30, 40, 50, 60, 70, 80, 90, 100,
                 150, 200, 250, 300, 350, 400, 450]
                )
#         self._plot_boxplot_global(data[2],2,
#         [20,40,60,80,100,150,200,250,300,350,400,450])
#         self._plot_boxplot_global(data[3],3,
#         [50,100,150,200,250,300,350,400,450,500,550,600])
        self._plot_percentile_global(data, 50)

    def run_global_recource(self):
        ############################
        # read and manipulate data #
        ############################
        read_option = {'dtype': float, 'delimiter': ',',
                       'skip_header': 0, 'names': True}
        data = self._read_all_information('global/',
                                        'MemCPUOverhead_*.stats', read_option)

        #############################
        # manipulate data for graph #
        #############################
        self._plot_resource_mean(data)

        #print data[5][50]['Memusrbinmongod'] + data[5][50]['CPUmanagerpy']
        #print data[5][50].dtype

    def run_detail_latency(self):

        ############################
        # read and manipulate data #
        ############################
        read_option = {'dtype': float, 'delimiter': ',',
                       'skip_header': 0, 'names': True}
        data = self._read_all_information('detail/',
                                          'details.stats', read_option)

        #############################
        # manipulate data for graph #
        #############################
        #self._plot_detail(data)
        self._show_mean_values(data)
        self._plot_detail_v3(data)
        self._plot_pie_chart(data)

    def run_compare(self):

        ############################
        # read and manipulate data #
        ############################
        read_option = {'dtype': float, 'delimiter': ',', 'skip_header': 1}
        data = self._read_all_information('global-1-250/',
                                          'stats*.log', read_option)
        data2 = self._read_all_information('global-1-250-90cloud/',
                                           'stats*.log', read_option)

        #############################
        # manipulate data for graph #
        #############################
#        self._plot_compare(data,data2,1,[(x+1)*10 for x in range(10)])
        self._plot_compare_percentile(data, data2, 50)
        self._plot_compare_percentile(data, data2, 75)
        self._plot_compare_percentile(data, data2, 95)

    def _read_all_information(self, home_path_suffix,
                              file_filter, read_option):
        """(str, str, dict) -> dict(dict(array))"""
        home_path = self.args.path + home_path_suffix
        data = {}

        # go through number of processes case
        for n_process_dir in os.listdir(home_path):

            # get number of processes
            nProcess = int(n_process_dir[n_process_dir.rfind('__') + 2:])
            # create further dictionary
            data[nProcess] = {}

            # go through number of inject rate case
            for inject_rate_dir in os.listdir(home_path + n_process_dir):
                # get inject rate
                inject_rate = int(inject_rate_dir[inject_rate_dir.rfind('__') +
                                                  2:])

                # temp list of arrays
                temp_list = []
                # go through all servers
                for path in glob(home_path + n_process_dir + '/' +
                                 inject_rate_dir + "/*/" + file_filter):
                    print path
                    temp_list.append(numpy.genfromtxt(path, **read_option))

                data[nProcess][inject_rate] = numpy.hstack(temp_list)

        return data

    def _show_mean_values(self, data):
        """(dict(dict(array)),) -> None"""

        for nProcess in sorted(data.iterkeys()):
            for inject_rate in sorted(data[nProcess].iterkeys()):
                print "=======%d process(es) at \
                       %d inject rate=======" % (nProcess, inject_rate)
                for name in sorted(data[nProcess][inject_rate].dtype.names):
                    values = data[nProcess][inject_rate][name]
                    masked_values = numpy.ma.masked_array(values,
                                                          numpy.isnan(values))
                    print name, numpy.mean(masked_values)

    def _plot_mean_global(self, data):
        """(dict(dict(array)),) -> None"""

        # set line pattern cycle
        from itertools import cycle
        lines = ['ko-', 'kx-', 'k+-', 'ks-']
        linecycler = cycle(lines)

        # create figure
        fig = plt.figure()

        # manipulate data and plot
        x_axis = sorted(data[data.keys()[0]].iterkeys())
        for nProcess in sorted(data.iterkeys()):
            y_axis = [numpy.mean(data[nProcess][inject_rate], axis=0) * 1000
                      for inject_rate in x_axis]
            # Plot
            plt.plot(x_axis, y_axis, next(linecycler),
                     label=str(nProcess) + ' process(es)')

        ###############
        # setup graph #
        ###############
        # set log scale
        plt.yscale('log')

        ax = fig.gca()

        # set xticks
        ax.set_xticks(filter(lambda x: x % 10 == 0, x_axis))
        # set yticks
        y_axis_tick = numpy.concatenate([numpy.arange(100, 10, -20),
                                         numpy.arange(1000, 100, -200),
                                         numpy.arange(10000, 1000, -2000)])
        ax.set_yticks(y_axis_tick)

        # enable manual tick on y axis
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

        # etc
        ax.set_title('Global latency (mean)')
        ax.set_xlabel('Queries per second (Poisson)')
        ax.set_ylabel('Query latency (millisecond)')
        plt.grid()
        plt.axis([0, x_axis[len(x_axis) - 1] + 50, 10, 3000])
        plt.legend(loc='lower left')
        plt.savefig('Global latency (mean).png')
        plt.show()

    def _plot_boxplot_global(self, data, Nprocess, masks = None):
        """(dict(array),list) -> None"""

        x_axis = masks
        # create figure
        fig = plt.figure(figsize=(14, 6), dpi=80)

        #plot boxplot
        plot_data = [data[inject_rate] * 1000 for inject_rate in x_axis]
        plt.boxplot(plot_data, sym='', positions=x_axis, widths=9, whis=0)

        # plot line from 75 percentile to 95 percentile
        data_percentile_100 = [numpy.percentile(data[inject_rate], 100) * 1000
                               for inject_rate in x_axis]
        data_percentile_95 = [numpy.percentile(data[inject_rate], 95) * 1000
                              for inject_rate in x_axis]
        data_percentile_75 = [numpy.percentile(data[inject_rate], 75) * 1000
                              for inject_rate in x_axis]

        for i in xrange(len(data_percentile_95)):
            plt.plot([x_axis[i], x_axis[i]],
                     [data_percentile_75[i], data_percentile_95[i]],
                     'k.--', markersize=1)

        plt.plot(x_axis, data_percentile_95, 'k.', markersize=12)
#         #plot mean
#         data_mean = [numpy.mean(data[inject_rate])*1000
#                      for inject_rate in x_axis]
#         plt.plot(x_axis,data_mean,'o')

        ###############
        # setup graph #
        ###############
        # set log scale
        plt.yscale('log')

        ax = fig.gca()

        # set xticks
        ax.set_xticks(filter(lambda x: x % 10 == 0, x_axis))
        # set yticks
        y_axis_tick = numpy.concatenate([numpy.arange(10, 1, -2),
                                         numpy.arange(100, 10, -20),
                                         numpy.arange(1000, 100, -200),
                                         numpy.arange(10000, 1000, -2000)])
        y_axis_tick = numpy.insert(y_axis_tick, 1, 30)

        ax.set_yticks(y_axis_tick)

        # enable manual tick on y axis
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

        # etc
#         ax.set_title('Global latency ( ' + str(Nprocess) +
#                      ' concurrent processes )')
        ax.set_xlabel('queries/sec')
        ax.set_ylabel('query latency (msec)')
        plt.grid()
        #plt.axis([25, x_axis[len(x_axis)-1]+50, 6, 4001])
        plt.axis([0, x_axis[len(x_axis) - 1] + 25, 5, 5001])
#        plt.axis([0, 110, 6, 1001])

        plt.savefig('Global latency (boxplot)( ' + str(Nprocess) +
                    ' concurrent processes ).png')
        plt.show()

    def _plot_percentile_global(self, data, percentile):
        """(dict(dict(array)), int) -> None"""

        # set line pattern cycle
        from itertools import cycle
        lines = ['ko-', 'kx-', 'k^-', 'ks-']
        linecycler = cycle(lines)
        fills = ['black', 'black', 'white', 'black']
        fillcycler = cycle(fills)

        # create figure
        fig = plt.figure()

        # manipulate data and plot 
        x_axis = sorted(data[data.keys()[0]].iterkeys())
        for nProcess in sorted(data.iterkeys()):
            y_axis = [numpy.percentile(data[nProcess][inject_rate],
                                       percentile, axis=0) * 1000
                      for inject_rate in x_axis]
            # Plot
            plt.plot(x_axis, y_axis, next(linecycler),
                     label=str(nProcess) + ' core(s) for query processing',
                     markerfacecolor=next(fillcycler))

        # set log scale
        plt.yscale('log')

        ax = fig.gca()

        # set xticks
        ax.set_xticks(filter(lambda x: x % 10 == 0, x_axis))

        # set yticks
        y_axis_tick = numpy.concatenate([numpy.arange(100, 10, -20),
                                         numpy.arange(1000, 100, -200),
                                         numpy.arange(10000, 1000, -2000)])
        y_axis_tick = numpy.insert(y_axis_tick, 1, 30)
        ax.set_yticks(y_axis_tick)

        # enable manual tick on y axis
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

        # etc
#        ax.set_title('Global latency ('+str(percentile)+'-percentile)')
        ax.set_xlabel('queries/sec')
        ax.set_ylabel('query latency (msec)')
        plt.grid()
#         plt.axis([25, x_axis[len(x_axis)-1], 10, 2500])
        plt.axis([25, 650, 17, 1100])
        plt.legend(loc='lower right')
        plt.savefig('Global latency (' + str(percentile) + '-percentile).png')
        plt.show()

    def _plot_resource_mean(self, data):
        """(dict(dict(ndarray)),) -> None"""

        # set line pattern cycle
        from itertools import cycle
        lines = ['ko-', 'kx-', 'k^-', 'ks-']
        linecycler = cycle(lines)
        fills = ['black', 'black', 'white', 'black']
        fillcycler = cycle(fills)
        # manipulate data and plot

        ############
        # plot CPU #
        ############
        # create figure
        fig = plt.figure(figsize=(14, 6), dpi=80)

        x_axis = sorted(data[data.keys()[0]].iterkeys())
        for nProcess in sorted(data.iterkeys()):
            y_axis = [numpy.mean(
                        data[nProcess][inject_rate]['CPUmanagerpy'] +
                        data[nProcess][inject_rate]['CPUusrbinmongod'] +
                        data[nProcess][inject_rate]['CPUsensorManagerpy'] +
                        data[nProcess][inject_rate]['CPUindexManagerpy'],
                        axis=0) / 24  # 24 numbers of CPU cores
                      for inject_rate in x_axis]
            # Plot
            plt.plot(x_axis, y_axis, next(linecycler),
                     label=str(nProcess) + ' core(s) for query processing',
                     markerfacecolor=next(fillcycler))

        ax = fig.gca()

        # set xticks
        ax.set_xticks(filter(lambda x: x % 10 == 0, x_axis))
        # set yticks
        ax.set_yticks(numpy.arange(0, 25, 0.5))

        # etc
#        ax.set_title('Resources usage (CPU) (mean)')
        ax.set_xlabel('queries/sec')
        ax.set_ylabel('CPU utilization (%)')
        plt.grid()
        #plt.axis([25, x_axis[len(x_axis)-1], 0, 14])
        plt.axis([0, 450, 0, 8])
#         plt.legend(loc='upper left')
        plt.savefig('Resources usage (CPU) (mean).png')
        plt.show()

        ###############
        # plot Memory #
        ###############
        # create figure
        fig = plt.figure()

        # plot query subsystem memory

        x_axis = sorted(data[data.keys()[0]].iterkeys())
        for nProcess in sorted(data.iterkeys()):
            y_axis = [numpy.mean(data[nProcess][inject_rate]['Memmanagerpy'],
                                 axis=0) / 100 * 64   # 64 numbers of Mem
                      for inject_rate in x_axis]
            # Plot
            plt.plot(x_axis, y_axis, next(linecycler),
                     label='QS ' + str(nProcess) + ' process(es)')

        #==============================
        # plot mongoDB memory
        lines = ['ko--', 'kx--', 'k+--', 'ks--']
        linecycler = cycle(lines)

        for nProcess in sorted(data.iterkeys()):
            y_axis = [numpy.mean(
                              data[nProcess][inject_rate]['Memusrbinmongod'],
                              axis=0
                              ) / 100 * 64  # 64 numbers of Mem
                      for inject_rate in x_axis]
            # Plot
            plt.plot(x_axis, y_axis, next(linecycler),
                     label='DB ' + str(nProcess) + ' process(es)')

        #==============================
        ax = fig.gca()

        # set xticks
        ax.set_xticks(filter(lambda x: x % 10 == 0, x_axis))
        # set yticks
        #ax.set_yticks(numpy.arange(1,25,1))

        # etc
#        ax.set_title('Resources usage (Memory) (mean)')
        ax.set_xlabel('Queries per second (Poisson)')
        ax.set_ylabel('Memory Overhead (GB)')
        plt.grid()
        #plt.axis([0, x_axis[len(x_axis)-1]+50, 0 ,0])
        plt.legend(loc='upper left')
        plt.savefig('Resources usage (Memory) (mean).png')
        plt.show()

    def _plot_detail_not_used(self, data):
        """(dict(dict(ndarray)),) -> None"""

        # set box pattern cycle
        from itertools import cycle
        boxs = ['b', 'g', 'r', 'c', 'm']
        boxcycler = cycle(boxs)

        # create figure
        fig = plt.figure()

        x_axis = sorted(data[data.keys()[0]].iterkeys())
        width = 7.0       # the width of the bars
        isLogScale = True

        for nProcess in sorted(data.iterkeys()):
            for inject_rate in x_axis:

                # ==== message transmission ====
                plot_data = numpy.concatenate(
                    (data[nProcess][inject_rate]['transmission_of_msg_type_0'],
                     data[nProcess][inject_rate]['transmission_of_msg_type_1'],
                     data[nProcess][inject_rate]['transmission_of_msg_type_2']
                     ))
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(
                                            plot_data,
                                            numpy.isnan(plot_data)
                                            )

#note : numpy.percentile(masked_plot_data.tolist(),95)*1000 for percentile
#note : numpy.max(masked_plot_data)*1000 for max
#note : numpy.mean(masked_plot_data)*1000 for mean
                bar1 = plt.bar(
                        inject_rate - 2 * width,
                        numpy.percentile(masked_plot_data.tolist(), 95) * 1000,
                        width, color=next(boxcycler), log=isLogScale
                        )
                dotplot = plt.plot(inject_rate - 1.5 * width,
                                   numpy.max(masked_plot_data) * 1000, 'k*')
                dotplot = plt.plot(inject_rate - 1.5 * width,
                                   numpy.mean(masked_plot_data) * 1000, 'ks')
                dotplot = plt.plot(inject_rate - 1.5 * width,
                                   numpy.median(masked_plot_data) * 1000, 'kx')

                # ==== queue time ====
                plot_data = data[nProcess][inject_rate]['Queue_time']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))

                bar2 = plt.bar(inject_rate-width, numpy.percentile(masked_plot_data.tolist(),95)*1000, width,color=next(boxcycler),log=isLogScale)                
                dotplot = plt.plot(inject_rate-0.5*width,numpy.max(masked_plot_data)*1000,'k*')
                dotplot = plt.plot(inject_rate-0.5*width,numpy.mean(masked_plot_data)*1000,'ks')      
                dotplot = plt.plot(inject_rate-0.5*width,numpy.median(masked_plot_data)*1000,'kx')     
                                      
                # ==== ranking ====
                plot_data = data[nProcess][inject_rate]['Ranking']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))

                bar3 = plt.bar(inject_rate, numpy.percentile(masked_plot_data.tolist(),95)*1000, width,color=next(boxcycler),log=isLogScale)                
                dotplot = plt.plot(inject_rate+0.5*width,numpy.max(masked_plot_data)*1000,'k*')
                dotplot = plt.plot(inject_rate+0.5*width,numpy.mean(masked_plot_data)*1000,'ks')           
                dotplot = plt.plot(inject_rate+0.5*width,numpy.median(masked_plot_data)*1000,'kx')                    
                 
                # ==== data retrival(DB access) ====
                plot_data = numpy.concatenate((data[nProcess][inject_rate]['index_DB_access_for_approx_match'],
                                       data[nProcess][inject_rate]['object_DB_access_for_approx_match']))
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))

                bar4 = plt.bar(inject_rate+width, numpy.percentile(masked_plot_data.tolist(),95)*1000, width,color=next(boxcycler),log=isLogScale)                 
                dotplot = plt.plot(inject_rate+1.5*width,numpy.max(masked_plot_data)*1000,'k*')
                dotplot = plt.plot(inject_rate+1.5*width,numpy.mean(masked_plot_data)*1000,'ks')
                dotplot = plt.plot(inject_rate+1.5*width,numpy.median(masked_plot_data)*1000,'kx')
                                
                # ==== echo aggregate ====
                plot_data = data[nProcess][inject_rate]['Aggregatoraggregate']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))

                bar5 = plt.bar(inject_rate+2*width, numpy.percentile(masked_plot_data.tolist(),95)*1000, width,color=next(boxcycler),log=isLogScale)          
                dotplot = plt.plot(inject_rate+2.5*width,numpy.max(masked_plot_data)*1000,'k*')
                dotplot = plt.plot(inject_rate+2.5*width,numpy.mean(masked_plot_data)*1000,'ks')        
                dotplot = plt.plot(inject_rate+2.5*width,numpy.median(masked_plot_data)*1000,'kx')          
                        
        ax = fig.gca()
         
        # set xticks
        ax.set_xticks(x_axis)
         
        # set yticks
        #y_axis_tick =numpy.concatenate([numpy.arange(100,10,-20),numpy.arange(1000,100,-200),numpy.arange(10000,1000,-2000)])
        #ax.set_yticks(y_axis_tick)
 
        # enable manual tick on y axis
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
         
        # etc
        ax.set_title('Local latency (95-percentile) ('+str(nProcess)+' concurrent processes)')
        ax.set_xlabel('Queries per second (Poisson)')
        ax.set_ylabel('Latency (millisecond)')
        plt.grid()
        plt.axis([25, x_axis[len(x_axis)-1]+25, 0.01, 10000])
        
        plt.legend((bar1[0], bar2[0],bar3[0], bar4[0], bar5[0]), 
                   ('message transmission', 'Sojourn time','ranking','data retrival(DB access)','echo aggregate')
                   ,loc='upper right',bbox_to_anchor=(0, 0, 1, 1), bbox_transform=plt.gcf().transFigure)
        
        plt.savefig('Local latency (95-percentile) ('+str(nProcess)+' concurrent processes).png')
        plt.show()       

    def _plot_detail_v2_not_used(self,data):
        """(dict(dict(ndarray)),) -> None"""
        
        # set box pattern cycle 
#         from itertools import cycle
#         boxs = ['b','g','r','c','m']
#         boxcycler = cycle(boxs)
        
        # create figure
        fig = plt.figure()
        plt.subplot(121)
        x_axis = sorted(data[data.keys()[0]].iterkeys())
        width = 30.0       # the width of the bars
        isLogScale = True
        
        for nProcess in sorted(data.iterkeys()):
            for inject_rate in x_axis:
                
                # ==== message transmission ====
                plot_data = numpy.concatenate((data[nProcess][inject_rate]['transmission_of_msg_type_0'],
                                       data[nProcess][inject_rate]['transmission_of_msg_type_1'],
                                       data[nProcess][inject_rate]['transmission_of_msg_type_2']))
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))
#                 print masked_plot_data.tolist()
#                 reduced_plot_data = numpy.ma.compress_cols(masked_plot_data)
#                 print reduced_plot_data
#                 print numpy.percentile(masked_plot_data.tolist(),95,axis=0)*1000

                #note : numpy.percentile(masked_plot_data.tolist(),95)*1000 for percentile
                #note : numpy.max(masked_plot_data)*1000 for max
                #note : numpy.mean(masked_plot_data)*1000 for mean                
                bar1 = plt.bar(inject_rate-2*width, numpy.mean(masked_plot_data)*1000, width,log=isLogScale,color="w", hatch='\\')
                dotplot = plt.plot(inject_rate-1.5*width,numpy.max(masked_plot_data)*1000,'k*')
                #dotplot = plt.plot(inject_rate-1.5*width,numpy.mean(masked_plot_data)*1000,'ks')
                dotplot = plt.plot(inject_rate-1.5*width,numpy.percentile(masked_plot_data.tolist(),95)*1000,'kx')

                # ==== queue time ====
                plot_data = data[nProcess][inject_rate]['Queue_time']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))

                bar2 = plt.bar(inject_rate-width, numpy.mean(masked_plot_data)*1000, width,log=isLogScale,color="w", hatch='+')                
                dotplot = plt.plot(inject_rate-0.5*width,numpy.max(masked_plot_data)*1000,'k*')
                #dotplot = plt.plot(inject_rate-0.5*width,numpy.mean(masked_plot_data)*1000,'ks')      
                dotplot = plt.plot(inject_rate-0.5*width,numpy.percentile(masked_plot_data.tolist(),95)*1000,'kx')     
                                      
                # ==== ranking ====
                plot_data = data[nProcess][inject_rate]['Ranking']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))

                bar3 = plt.bar(inject_rate, numpy.mean(masked_plot_data)*1000, width,log=isLogScale,color="w", hatch='x')                
                dotplot = plt.plot(inject_rate+0.5*width,numpy.max(masked_plot_data)*1000,'k*')
                #dotplot = plt.plot(inject_rate+0.5*width,numpy.mean(masked_plot_data)*1000,'ks')           
                dotplot = plt.plot(inject_rate+0.5*width,numpy.percentile(masked_plot_data.tolist(),95)*1000,'kx')                    
                 
                # ==== data retrival(DB access) ====
                plot_data = numpy.concatenate((data[nProcess][inject_rate]['index_DB_access_for_approx_match'],
                                       data[nProcess][inject_rate]['object_DB_access_for_approx_match']))
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))

                bar4 = plt.bar(inject_rate+width, numpy.mean(masked_plot_data)*1000, width,log=isLogScale,color="w", hatch='|')                 
                dotplot = plt.plot(inject_rate+1.5*width,numpy.max(masked_plot_data)*1000,'k*')
                #dotplot = plt.plot(inject_rate+1.5*width,numpy.mean(masked_plot_data)*1000,'ks')
                dotplot = plt.plot(inject_rate+1.5*width,numpy.percentile(masked_plot_data.tolist(),95)*1000,'kx')
                                
                # ==== echo aggregate ====
                plot_data = data[nProcess][inject_rate]['Aggregatoraggregate']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))

                bar5 = plt.bar(inject_rate+2*width, numpy.mean(masked_plot_data)*1000, width,log=isLogScale,color="w", hatch='o')          
                dotplot = plt.plot(inject_rate+2.5*width,numpy.max(masked_plot_data)*1000,'k*')
                #dotplot = plt.plot(inject_rate+2.5*width,numpy.mean(masked_plot_data)*1000,'ks')        
                dotplot = plt.plot(inject_rate+2.5*width,numpy.percentile(masked_plot_data.tolist(),95)*1000,'kx')          
                        
        ax = fig.gca()
         
        # set xticks
        ax.set_xticks(x_axis)
         
        # set yticks
        #y_axis_tick =numpy.concatenate([numpy.arange(100,10,-20),numpy.arange(1000,100,-200),numpy.arange(10000,1000,-2000)])
        #ax.set_yticks(y_axis_tick)
 
        # enable manual tick on y axis
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
         
        # etc
        ax.set_title('Local latency (mean + 95 + max)  ('+str(nProcess)+' concurrent processes)')
        ax.set_xlabel('Queries per second (Poisson)')
        ax.set_ylabel('Latency (millisecond)')
        plt.grid()
        plt.axis([100, 500, 0.01, 10000])
        
        plt.legend((bar1[0], bar2[0],bar3[0], bar4[0], bar5[0]), 
                   ('message transmission', 'Sojourn time','ranking','data retrival(DB access)','echo aggregate')
                   ,loc=2, borderaxespad=0.,bbox_to_anchor=(1.05, 1)) #, bbox_transform=plt.gcf().transFigure
        
        plt.savefig('Local latency (mean + 95 + max) ('+str(nProcess)+' concurrent processes).png')
        plt.show()   
            
    def _plot_detail_v3(self,data):
        """(dict(dict(ndarray)),) -> None"""
        
        # set hatch pattern cycle 
        from itertools import cycle
        #colors = ['%f' % gray for gray in numpy.arange(1,0,-1.0/len(data[data.keys()[0]].keys()))]
        n = len(data[data.keys()[0]].keys())
        colors = ['%f' % (i/float(n)) for i in range(n,0,-1)]
        colorcycler = cycle(colors)

        # create figure
        fig = plt.figure()
        n_rate = len(data[data.keys()[0]].keys())
        width = 80/n_rate       # the width of the bars
        isLogScale = True
        
        for nProcess in sorted(data.iterkeys()):
            # ==== message transmission ====
            x=100
            i=-n_rate/2-1
            for inject_rate in sorted(data[nProcess].iterkeys()):
                i+=1
                plot_data = numpy.concatenate((data[nProcess][inject_rate]['transmission_of_msg_type_0'],
                                       data[nProcess][inject_rate]['transmission_of_msg_type_1'],
                                       data[nProcess][inject_rate]['transmission_of_msg_type_2']))
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))
                
                bar1 = plt.bar(x+i*width, numpy.mean(masked_plot_data)*1000, width,log=isLogScale,color=next(colorcycler))
  
            # ==== queue time ====
            x=200
            i=-n_rate/2-1
            for inject_rate in sorted(data[nProcess].iterkeys()):
                i+=1    
                plot_data = data[nProcess][inject_rate]['Queue_time']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))  

                bar1 = plt.bar(x+i*width, numpy.mean(masked_plot_data)*1000, width,log=isLogScale,color=next(colorcycler))
 
            # ==== ranking ====
            x=300
            i=-n_rate/2-1
            for inject_rate in sorted(data[nProcess].iterkeys()):
                i+=1    
                plot_data = data[nProcess][inject_rate]['Ranking']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data)) 
 
                bar1 = plt.bar(x+i*width, numpy.mean(masked_plot_data)*1000, width,log=isLogScale,color=next(colorcycler))


            # ==== data retrival(DB access) ====
            x=400
            i=-n_rate/2-1
            for inject_rate in sorted(data[nProcess].iterkeys()):
                i+=1              
                plot_data = numpy.concatenate((data[nProcess][inject_rate]['index_DB_access_for_approx_match'],
                                       data[nProcess][inject_rate]['object_DB_access_for_approx_match']))
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))
                
                bar1 = plt.bar(x+i*width, numpy.mean(masked_plot_data)*1000, width,log=isLogScale,color=next(colorcycler))

            # ==== echo aggregate ====
            x=500
            i=-n_rate/2-1
            for inject_rate in sorted(data[nProcess].iterkeys()):
                i+=1                          
                plot_data = data[nProcess][inject_rate]['Aggregatoraggregate']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))
                
                bar1 = plt.bar(x+i*width, numpy.mean(masked_plot_data)*1000, width,log=isLogScale,color=next(colorcycler))
    
    
            ax = fig.gca()
            # set xticks
            ax.set_xticks([100,200,300,400,500])
            ax.set_xticklabels(['message transmission', 'sojourn time','matching and ranking','DB access','aggregate'])
            # set yticks
            #y_axis_tick =numpy.concatenate([numpy.arange(100,10,-20),numpy.arange(1000,100,-200),numpy.arange(10000,1000,-2000)])
            #ax.set_yticks(y_axis_tick)
     
            # enable manual tick on y axis
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
             
            # etc
            ax.set_title('Local latency (mean)  ('+str(nProcess)+' concurrent processes)')
            ax.set_xlabel('operations')
            ax.set_ylabel('Latency (millisecond)')
            plt.grid()
            plt.axis([0, 600, 0.01, 10000])
            
            plt.legend(["%d queries/sec" % x for x in sorted(data[nProcess].iterkeys())]
                        ,loc="upper right") 
             
            plt.savefig('Local latency (mean + 95 + max) ('+str(nProcess)+' concurrent processes).png')
            plt.show()       
            
    def _plot_pie_chart(self,data):
        """(dict(dict(ndarray)),) -> None"""

        x_axis = sorted(data[data.keys()[0]].iterkeys())

        name_list = ['message transmission', 'sojourn time','matching and ranking','DB access','aggregate']
        
        for nProcess in sorted(data.iterkeys()):
            for inject_rate in x_axis:
                mean_data = []
                # ===========message tranmission===========
                plot_data = numpy.concatenate((data[nProcess][inject_rate]['transmission_of_msg_type_0'],
                                       data[nProcess][inject_rate]['transmission_of_msg_type_1'],
                                       data[nProcess][inject_rate]['transmission_of_msg_type_2']))
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))
                mean_data.append(numpy.mean(masked_plot_data)*1000)
                
                # ===========queue time===========               
                plot_data = data[nProcess][inject_rate]['Queue_time']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))                  
                mean_data.append(numpy.mean(masked_plot_data)*1000)
                
                # ===========maching and ranking===========
                plot_data = data[nProcess][inject_rate]['Ranking']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data)) 
                mean_data.append(numpy.mean(masked_plot_data)*1000)
                 
                # ===========DB access===========
                plot_data = numpy.concatenate((data[nProcess][inject_rate]['index_DB_access_for_approx_match'],
                                       data[nProcess][inject_rate]['object_DB_access_for_approx_match']))
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))
                mean_data.append(numpy.mean(masked_plot_data)*1000)
                                
                # ===========aggregate===========                                
                plot_data = data[nProcess][inject_rate]['Aggregatoraggregate']
                # remove NaN by masking
                masked_plot_data = numpy.ma.masked_array(plot_data,numpy.isnan(plot_data))
                mean_data.append(numpy.mean(masked_plot_data)*1000)
                
                fig = plt.figure()
                gs = matplotlib.gridspec.GridSpec(1, 2,width_ratios=[5,1])
 
                ax1 = plt.subplot(gs[0])
                
                plt.pie(mean_data, labels=name_list, shadow=False,autopct='%1.1f%%',colors = ['%f' % (i/float(5)) for i in range(5,0,-1)])
                ax = fig.gca()
                ax.set_title('mean latency ('+str(inject_rate)+' rate)')
                 
                plt.savefig('mean latency (pie) ('+str(inject_rate)+' rate).png')
                plt.show() 

    def _plot_compare(self,data,data2,Nprocess,marked_load):
        """(dict(dict(ndarray)),dict(dict(ndarray)),int,list) -> None"""
        for inject_rate in marked_load:
            fig = plt.figure()
            # data
            plot_data_1 = data[Nprocess][inject_rate]
            plot_data_2 = data2[Nprocess][inject_rate]
            x_axis = [5,10]
            
            #plot boxplot
            plot_data = [plot_data_1*1000,plot_data_2*1000]
            plt.boxplot(plot_data,sym='',positions=x_axis, widths=3, whis=0)
            
            #plot whiskle
            data_percentile_95 = [numpy.percentile(plot_data_1,95)*1000,numpy.percentile(plot_data_2,95)*1000]
            data_percentile_75 = [numpy.percentile(plot_data_1,75)*1000,numpy.percentile(plot_data_2,75)*1000]
             
            for i in xrange(len(data_percentile_95)):
                plt.plot([x_axis[i],x_axis[i]],[data_percentile_75[i],data_percentile_95[i]],'k.--',markersize=1)
            #plt.plot(x_axis,data_percentile_100,'k_',markersize=12)        
            plt.plot(x_axis,data_percentile_95,'k.',markersize=12)
            
            plt.yscale('log')
         
            ax = fig.gca()
            
            # set xticks
            ax.set_xticks(x_axis)
            ax.set_xticklabels(['normal cloud', '90% loaded cloud'])
            # set yticks
            y_axis_tick =numpy.concatenate([numpy.arange(10,1,-2),numpy.arange(100,10,-20),numpy.arange(1000,100,-200),numpy.arange(10000,1000,-2000)])
            ax.set_yticks(y_axis_tick)
     
            # enable manual tick on y axis
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
             
            # etc
            ax.set_title('Global latency ( '+str(inject_rate)+' queries/sec)')
            ax.set_ylabel('query latency (msec)')
            plt.grid()
            #plt.axis([25, x_axis[len(x_axis)-1]+50, 6, 4001])        
            plt.axis([0, 15, 6, 1001])
            
            plt.savefig('Global latency ( '+str(inject_rate)+' queries per sec).png')
            plt.show()

           
    def _plot_compare_percentile(self,data,data2,percentile):
        """(dict(dict(ndarray)),dict(dict(ndarray))) -> None"""
        # set line pattern cycle 
        from itertools import cycle
        lines = ['ko-', 'kx-', 'k+-', 'ks-']
        linecycler = cycle(lines)
         
        # create figure
        fig = plt.figure()
         
        # manipulate data and plot 
        x_axis = sorted(data[data.keys()[0]].iterkeys())
        for nProcess in sorted(data.iterkeys()):
            #==========data one==============
#             y_axis = [numpy.mean(data[nProcess][inject_rate])*1000 for inject_rate in x_axis] 
#             # Plot
#             plt.plot(x_axis,y_axis,next(linecycler),label='mean, real')
            
            y_axis = [numpy.percentile(data[nProcess][inject_rate], percentile, axis=0)*1000 for inject_rate in x_axis] 
            # Plot
            plt.plot(x_axis,y_axis,next(linecycler),label='under utilized')
            
#             y_axis = [numpy.percentile(data[nProcess][inject_rate], 95, axis=0)*1000 for inject_rate in x_axis] 
#             # Plot
#             plt.plot(x_axis,y_axis,next(linecycler),label='95 percentile, real')
            
            #==========data two==============
#             y_axis = [numpy.mean(data2[nProcess][inject_rate])*1000 for inject_rate in x_axis] 
#             # Plot
#             plt.plot(x_axis,y_axis,next(linecycler),label='mean, real')
            
            y_axis = [numpy.percentile(data2[nProcess][inject_rate], percentile, axis=0)*1000 for inject_rate in x_axis] 
            # Plot
            plt.plot(x_axis,y_axis,next(linecycler),label='highly utilized')
            
#             y_axis = [numpy.percentile(data2[nProcess][inject_rate], 95, axis=0)*1000 for inject_rate in x_axis] 
#             # Plot
#             plt.plot(x_axis,y_axis,next(linecycler),label='95 percentile, real')
         
        # set log scale
        plt.yscale('log')
         
        ax = fig.gca()
         
        # set xticks
        ax.set_xticks(x_axis)
         
        # set yticks
        y_axis_tick =numpy.concatenate([numpy.arange(100,10,-20),numpy.arange(1000,100,-200),numpy.arange(10000,1000,-2000)])
        ax.set_yticks(y_axis_tick)
 
        # enable manual tick on y axis
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
         
        # etc
        ax.set_title('Global latency compared ('+str(percentile)+'-percentile)')
        ax.set_xlabel('queries/sec')
        ax.set_ylabel('query latency (msec)')
        plt.grid()
#         plt.axis([25, x_axis[len(x_axis)-1], 10, 2500])
        plt.axis([25,250, 10, 2500])
        plt.legend(loc='upper left')
        plt.savefig('Global latency compared ('+str(percentile)+'-percentile).png')
        plt.show()
        
                
def main():
    
    # Read command arguments
    try:
        args = get_args()
    except IOError as (errno, strerror):
        print "IOError({0}): {1}".format(errno,strerror)
    
    # run the analyzer
    A = Analyzer(args)
    
    if args.global_lat:
        A.run_global_latency()
    if args.resource:
        A.run_global_recource()
    if args.detail:
        A.run_detail_latency()
    if args.compare:
        A.run_compare()
        
    #END    
        
if __name__ == "__main__" :
    exit(main())
    