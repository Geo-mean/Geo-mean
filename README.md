# Geo-mean

An open-source Python application for the processing, correction, and visualization of geochemical data.

<img width="1251" height="938" alt="image" src="https://github.com/user-attachments/assets/4836f26e-d07e-4ae7-83a5-b5171208f7ba" />


## Introduction

Geo-mean is a free, open-source application designed to address common challenges in geochemical data processing and analysis, including outlier detection, correction for uneven spatial and temporal sample distribution, and trend analysis.

**Geo-mean can run on all mainstream operating systems**, including Windows, macOS, and GNU/Linux.

**Geo-mean does not rely on any commercial software**, such as MS Excel, MATLAB, or IBM SPSS. It provides a simple and user-friendly graphical interface, allowing users without any programming background to complete the entire workflow — from data purification to statistical analysis and visualization.

## Main Features

Geo-mean provides both basic data processing functions and newly developed methods:

**Basic Functions**
- Outlier Elimination (percentile method, standard deviation method, IQR method, custom range)
- Conditional Filtering (with missing-value handling)

**Newly Developed Methods**
- Outlier Elimination for X-intervals — detects and removes outliers within user-defined intervals along an X-axis variable (e.g., age), addressing the limitations of global outlier detection
- Geographic Gridding — corrects for uneven spatial and temporal sample distribution through joint spatial–temporal grid-based resampling
- Moving Average Analysis — a sliding-window approach that produces smoother, more statistically robust trends in sparsely sampled time intervals
- Bootstrap Median Window — applies Bootstrap resampling within a sliding window to calculate the median and confidence interval, offering a more robust alternative to the mean

**Auxiliary Visualization**
- Plotting (X–Y) — quick scatter/line plots for reviewing raw or processed data

A full description of these functions, together with example datasets and figures, can be found in our manuscript (citation below).

## Citation

If you use Geo-mean in your research, please cite:

```
Hao, Y.-H., Liu, H., Geo-mean: an integrated toolkit for outlier detection, spatiotemporal
resampling, and trend analysis of geochemical data, Geoscience Frontiers (in review).
```

*(This section will be updated with the full citation and DOI once the manuscript is published.)*

## Installation

### Option 1: Standalone application (recommended)

Download the packaged executable for your operating system (Windows / macOS / GNU/Linux) from the [Releases](../../releases) page. After downloading and unzipping, double-click the executable to launch Geo-mean — no additional installation is required.

### Option 2: Run from source (for Python users)

If you want to use Geo-mean as a Python module or modify its source code, you will need Python 3 and the following dependencies:

```
pandas
numpy
matplotlib
tksheet
openpyxl
Pillow
```

Install the dependencies with:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python main.py
```

## Data Files

Geo-mean accepts MS Excel XLSX and CSV files as input. Example datasets are provided in the [`DataFileSamples`](DataFileSamples) folder — feel free to use them to try out the software before loading your own data.

## Output

- Processed data and statistical results: XLSX or CSV
- Generated figures: PNG, SVG, or PDF

## Bug Reports & Feedback

Geo-mean is still under active development, and bugs are inevitable. If you encounter a problem:

1. Open an [Issue](../../issues) in this repository.
2. Please include: the Geo-mean version you are using, a screenshot or description of the error, and — if possible — a sample data file that triggers the issue.

Feature requests are also welcome — please open an Issue describing the function you'd like to see, ideally with a reference or example of how it should work.

## Contributing

Geo-mean is open source, and users with Python experience are welcome to contribute new functions or improvements. Feel free to fork this repository and submit a pull request.

## License

Geo-mean is released under the [GNU General Public License v3.0](LICENSE). You are free to use, share, and modify it under the same terms.

## Contact

For questions not related to bugs, feel free to reach out via liuhe@qdio.ac.cn.
