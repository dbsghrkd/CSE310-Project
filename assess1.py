import matplotlib.pyplot as plt
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import httpx

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

def measure_performance(url):
    timings = {'load_time': [], 'ttfb': [], 'download_time': [], 'rtt': [], 'throughput': []}
    
    for _ in range(3):  
        chrome_options = Options()
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--incognito")  
        chrome_options.add_argument("--enable-quic")  
        chrome_options.add_argument("--quic-version=h3-23")  
        
        chrome_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        
        driver.get(url)
        
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
        
        driver.quit()
    
    average_timings = {k: sum(v) / len(v) for k, v in timings.items()}
    return average_timings

sites = {
    "google.com": {
        "HTTP/2": "https://www.google.com",
        "HTTP/3": "https://www.google.com"
    },
    "facebook.com": {
        "HTTP/2": "https://www.facebook.com",
        "HTTP/3": "https://www.facebook.com"
    },
    "youtube.com": {
        "HTTP/2": "https://www.youtube.com",
        "HTTP/3": "https://www.youtube.com"
    },
    "instagram.com": {
        "HTTP/2": "https://www.instagram.com",
        "HTTP/3": "https://www.instagram.com"
    },
    "amazon.com": {
        "HTTP/2": "https://www.amazon.com",
        "HTTP/3": "https://www.amazon.com"
    },
}

results = {
    "google.com": {},
    "facebook.com": {},
    "youtube.com": {},
    "instagram.com": {},
    "amazon.com": {},
}

for site, protocols in sites.items():
    for protocol, url in protocols.items():
        protocol_detected = get_protocol(url)
        if protocol_detected != protocol:
            print(f"Warning: Expected {protocol} but got {protocol_detected} for {url}")
        results[site][protocol] = measure_performance(url)

def plot_metric_comparison(results, metric, start, end):
    sites = list(results.keys())[start:end]
    http2_data = [results[site]['HTTP/2'][metric] for site in sites]
    http3_data = [results[site]['HTTP/3'][metric] for site in sites]

    x = np.arange(len(sites)) 

    fig, ax1 = plt.subplots(figsize=(12, 6)) 
    width = 0.35  

    rects1 = ax1.bar(x - width/2, http2_data, width, label='HTTP/2')
    rects2 = ax1.bar(x + width/2, http3_data, width, label='HTTP/3')

    ax1.set_xlabel('Sites')
    ax1.set_ylabel(metric.capitalize().replace('_', ' '))
    ax1.set_title(f'HTTP/2 vs HTTP/3 {metric.capitalize().replace("_", " ")} Comparison')
    ax1.set_xticks(x)
    ax1.set_xticklabels(sites, rotation=45, ha='right')
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
site_chunks = [range(0, 10), range(10, 20)]

for metric in metrics:
    for chunk in site_chunks:
        plot_metric_comparison(results, metric, chunk.start, chunk.stop)
