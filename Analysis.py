import matplotlib.pyplot as plt
import numpy as np

# Websites and their load times as provided
websites = [
    'alibaba.com', 'bbc.com', 'linkedin.com', 'netflix.com', 'wikipedia.org',
    'amazon.com', 'facebook.com', 'google.com', 'instagram.com', 'youtube.com',
    'apple.com', 'booking.com', 'dropbox.com', 'spotify.com', 'stackoverflow.com',
    'bing.com', 'cloudflare.com', 'pinterest.com', 'roblox.com', 'wordpress.org'
]

# TTFB times for HTTP/2 for six different scenarios and here is just one dataset for show. we tried all cases using these methods
http2_data = {
    'delay0_rate0': [172.0, 10.3, 265.3, 302.3, 136.7, 449.0, 236.3, 125.7, 355.7, 94.3,
    25.0, 1239.7, 1261.7, 74.3, 512.0, 28.0, 58.3, 404.0, 298.0, 186.7]
}

# TTFB times for HTTP/3 for six different scenarios
http3_data = {
    'delay0_rate0': [160.0, 11.3, 308.0, 328.3, 158.0, 654.3, 205.0, 139.7, 323.0, 78.3,
    25.3, 1019.3, 858.7, 79.3, 498.0, 31.3, 60.0, 391.3, 230.3, 191.0
]
}

def plot_load_times(config):
    http2_times = http2_data[config]
    http3_times = http3_data[config]
    x = np.arange(len(websites))  # Label locations
    width = 0.35  # Bar width

    plt.figure(figsize=(14, 7))
    plt.bar(x - width/2, http2_times, width, label='HTTP/2')
    plt.bar(x + width/2, http3_times, width, label='HTTP/3')
    plt.xlabel('Websites')
    plt.ylabel('TTFB (ms)')
    plt.title(f'TTFB for {config}')
    plt.xticks(x, websites, rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()

# Call function to plot for the 'delay10_rate10' configuration
plot_load_times('delay0_rate0')
