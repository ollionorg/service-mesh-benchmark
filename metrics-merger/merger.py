#!/usr/bin/env python3

import json
from sys import argv, exit
from os import putenv

from collections import OrderedDict

from prometheus_http_client import Prometheus
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway


def metrics_iter(p, query):
    m = p.query(metric=query)
    j = json.loads(m)
    return iter(j.get("data",{}).get("result"))
# --

def get_completed_runs(p, mesh):
    ret=[]

    for i in metrics_iter(p,
        'wrk2_benchmark_progress{status="done",exported_job="%s"}' % (mesh,)):
       ret.append(i["metric"]["run"])

    return ret
# --

def get_requested_rps(p, mesh, run):
    m = p.query(
         metric='wrk2_benchmark_run_requested_rps{run="%s",exported_job="%s"}'
                 % (run, mesh))
    j = json.loads(m)
    return j.get("data",{}).get("result")[0]["value"][1]
# --

def get_latency_histogram(run,detailed=False):
    # return histogram of a single run as dict 
    # {<percentile>: <latency in ms>, ...}

    ret=OrderedDict()

    if detailed:
        detailed="detailed_"
    else:
        detailed=""

    for i in metrics_iter(p,
                    'wrk2_benchmark_latency_%sms{run="%s"}' %(detailed,run,)):
       ret[float(i["metric"]["p"])] = float(i["value"][1])

    return ret
# --

def get_latency_histograms(p, mesh, detailed=False):
    # get all runs for a given service mesh
    histograms={}
    for run in get_completed_runs(p, mesh):
        h = get_latency_histogram(run, detailed)
        for perc,lat in h.items():
            if histograms.get(perc, False):
                histograms[perc][run]=lat
            else:
                histograms[perc] = OrderedDict({run:lat})

    # sort runs' latencies for each percentile
    for perc in histograms.keys():
        histograms[perc] = {k: v for k, v in 
                    sorted(histograms[perc].items(), key=lambda item: item[1])}

    return histograms
# --

def create_summary_gauge(p, mesh, r, detailed=False):
    histograms = get_latency_histograms(p, mesh, detailed)

    if detailed:
        detailed="detailed_"
    else:
        detailed=""

    g = Gauge('wrk2_benchmark_summary_latency_%sms' % (detailed,),
              '%s latency summary' % (mesh,),
                labelnames=["p","source_run", "requested_rps"], registry=r)

    percs_count=0; runs_count=0
    run_requested_rps={}

    # create latency entries for all runs, per percentile
    for perc, latencies in histograms.items():
        percs_count = percs_count + 1
        runs_count=0
        for run, lat in latencies.items():
            if run in run_requested_rps:
                rps = run_requested_rps[run]
            else:
                rps = get_requested_rps(p, mesh, run)
                run_requested_rps[run] = rps
            runs_count = runs_count + 1
            g.labels(p=perc, source_run=run, requested_rps=rps).set(lat)

    return g, percs_count, runs_count
# --

#
# -- main --
#

if 3 != len(argv):
    print(
       'Command line error: Prometheus URL and push gateway are required.')
    print('Usage:')
    print('  %s <Prometheus server URL> <Prometheus push gateway host:port>'
            % (argv[0],))
    exit(1)

prometheus_url = argv[1]
pgw_url = argv[2]

putenv('PROMETHEUS_URL', prometheus_url)
p = Prometheus()

for mesh in ["bare-metal", "svcmesh-linkerd", "svcmesh-istio"]:

    r = CollectorRegistry()
    workaround = mesh
    g, percs, runs = create_summary_gauge(p, mesh, r)
    dg, dpercs, druns = create_summary_gauge(p, mesh, r, detailed=True)

    print("%s: %d runs with %d percentiles (coarse)" % (mesh, runs, percs))
    print("%s: %d runs with %d percentiles (detailed)" % (mesh, druns, dpercs))

    push_to_gateway(pgw_url, job=mesh,
            grouping_key={"instance":"emojivoto"}, registry=r)