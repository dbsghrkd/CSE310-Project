import matplotlib.pyplot as plt
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import httpx
import subprocess

def get_protocol(url):
    try:
        with httpx.Client(http2=True) as client:
            response = client.get(url)
            if response.http_version == "HTTP/2":
                return "HTTP/2"
            elif response.http_version == "HTTP/1.1":
                return "HTTP/1.1"
        with httpx.Client(http2=False, http3=True) as client:
            response = client.get(url)
            if response.http_version == "HTTP/3":
                return "HTTP/3"
    except Exception as e:
        print(f"Error checking protocol for {url}: {e}")
    return "Unknown"

def measure_performance(url, use_quic=False):
    timings = {'load_time': [], 'ttfb': [], 'download_time': [], 'rtt': [], 'throughput': []}
    
    for i in range(3):  
        chrome_options = Options()
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--incognito")  
        if use_quic:
            chrome_options.add_argument("--enable-quic")  
            chrome_options.add_argument("--quic-version=h3-23")  

        chrome_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        
        try:
            driver.get(url)
            print(f"Accessing {url} - Attempt {i+1}")
            
            performance = driver.execute_script("""
                const timing = window.performance.timing;
                const loadTime = timing.loadEventEnd - timing.navigationStart;
                const ttfb = timing.responseStart - timing.requestStart;
                const downloadTime = timing.responseEnd - timing.responseStart;
                const rtt = timing.responseEnd - timing.fetchStart;
                return {
                    loadTime: loadTime > 0 ? loadTime : 0,
                    ttfb: ttfb > 0 ? ttfb : 0,
                    downloadTime: downloadTime > 0 ? downloadTime : 0,
                    rtt: rtt > 0 ? rtt : 0
                };
            """)
            
            resources = driver.execute_script("""
                return window.performance.getEntriesByType('resource')
                .map(resource => ({
                    transferSize: resource.transferSize,
                    duration: resource.duration
                }));
            """)
            
            total_transfer_size = sum(resource['transferSize'] for resource in resources if resource['transferSize'] > 0)
            total_duration = sum(resource['duration'] for resource in resources if resource['duration'] > 0)
            throughput = total_transfer_size / total_duration if total_duration > 0 else 0
            
            timings['load_time'].append(performance['loadTime'])
            timings['ttfb'].append(performance['ttfb'])
            timings['download_time'].append(performance['downloadTime'])
            timings['rtt'].append(performance['rtt'])
            timings['throughput'].append(throughput)
        
        except Exception as e:
            print(f"Error during performance measurement for {url}: {e}")
        
        finally:
            driver.quit()
    
    average_timings = {k: sum(v) / len(v) for k, v in timings.items() if v}
    print(f"Measured performance for {url} - {average_timings}")
    return average_timings

sites = {
    "bing.com": {
        "HTTP/2": "https://www.bing.com",
        "HTTP/3": "https://www.bing.com"
    },
    "wordpress.org": {
        "HTTP/2": "https://www.wordpress.org",
        "HTTP/3": "https://www.wordpress.org"
    },
    "pinterest.com": {
        "HTTP/2": "https://www.pinterest.com",
        "HTTP/3": "https://www.pinterest.com"
    },
    "roblox.com": {
        "HTTP/2": "https://www.roblox.com",
        "HTTP/3": "https://www.roblox.com"
    },
    "cloudflare.com": {
        "HTTP/2": "https://www.cloudflare.com",
        "HTTP/3": "https://www.cloudflare.com"
    },
}

results = {
    "bing.com": {},
    "wordpress.org": {},
    "pinterest.com": {},
    "roblox.com": {},
    "cloudflare.com": {},
}

for site, protocols in sites.items():
    for protocol, url in protocols.items():
        protocol_detected = get_protocol(url)
        if protocol_detected != protocol:
            print(f"Warning: Expected {protocol} but got {protocol_detected} for {url}")
        use_quic = protocol == "HTTP/3"
        results[site][protocol] = measure_performance(url, use_quic)

def plot_metric_comparison(results, metric, start, end):
    site_list = list(results.keys())[start:end]
    http2_data = [results[site]['HTTP/2'][metric] for site in site_list]
    http3_data = [results[site]['HTTP/3'][metric] for site in site_list]

    x = np.arange(len(site_list)) 

    fig, ax1 = plt.subplots(figsize=(12, 6))  
    width = 0.35 

    rects1 = ax1.bar(x - width/2, http2_data, width, label='HTTP/2')
    rects2 = ax1.bar(x + width/2, http3_data, width, label='HTTP/3')

    ax1.set_xlabel('Sites')
    ax1.set_ylabel(metric.capitalize().replace('_', ' '))
    ax1.set_title(f'HTTP/2 vs HTTP/3 {metric.capitalize().replace("_", " ")} Comparison')
    ax1.set_xticks(x)
    ax1.set_xticklabels(site_list, rotation=45, ha='right')
    ax1.legend()

    def add_labels(rects, ax):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  
                        textcoords="offset points",
                        ha='center', va='bottom')

    add_labels(rects1, ax1)
    add_labels(rects2, ax1)

    plt.tight_layout()
    plt.show()

metrics = ['load_time', 'ttfb', 'download_time', 'rtt', 'throughput']
site_chunks = [range(0, 5)]  

for metric in metrics:
    for chunk in site_chunks:
        plot_metric_comparison(results, metric, chunk.start, chunk.stop)
