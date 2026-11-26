%% Self-contained MATLAB figures for the Top-k substitution-cipher paper
% All plotted data are embedded below. This script does not call readtable,
% load, csvread, jsondecode, or any external data source.
%
% Generated figures:
%   1. Hit@k versus ciphertext length, with 95% Wilson intervals
%   2. MRR versus ciphertext length, with 95% bootstrap intervals
%   3. Observed rank versus oracle-score rank, with IQR and retention
%   4. Score gap versus ciphertext length, with 95% bootstrap intervals
%   5. Failure-category breakdown
%   6. Archive-capacity sensitivity, with 95% Wilson intervals
%
% MATLAB version: R2020a or newer is recommended for exportgraphics.

clear;
clc;
close all;

%% Output and visual settings
scriptDir = fileparts(mfilename('fullpath'));
outputDir = fullfile(scriptDir, '..', 'results', 'matlab_paper_figures');
if ~exist(outputDir, 'dir')
    mkdir(outputDir);
end

figureVisible = 'on';  % Change to 'off' for unattended batch rendering.
pngResolution = 600;

set(groot, ...
    'defaultAxesFontName', 'Times New Roman', ...
    'defaultAxesFontSize', 12, ...
    'defaultAxesLineWidth', 1.0, ...
    'defaultLineLineWidth', 2.2, ...
    'defaultTextFontName', 'Times New Roman', ...
    'defaultTextInterpreter', 'none', ...
    'defaultAxesTickLabelInterpreter', 'none', ...
    'defaultLegendInterpreter', 'none');

colors = [
    0.0000 0.4470 0.7410
    0.8500 0.3250 0.0980
    0.4660 0.6740 0.1880
    0.4940 0.1840 0.5560
    0.9290 0.6940 0.1250
    0.3010 0.7450 0.9330
];
markers = {'o', 's', '^', 'd', 'v', 'p'};

%% Embedded main-experiment data
% Rows follow ciphertextLengths.
% Hit columns are Hit@1, Hit@5, Hit@10, Hit@50, Hit@100, Hit@1000.
ciphertextLengths = [25 40 50 60 75 80 100 150 200 300 500];

hitRate = [
    0.00200000 0.00200000 0.00200000 0.00400000 0.00400000 0.00400000
    0.00200000 0.00300000 0.00400000 0.00500000 0.00500000 0.00500000
    0.01900000 0.03200000 0.03500000 0.03700000 0.03700000 0.03800000
    0.02900000 0.06500000 0.07200000 0.08400000 0.08400000 0.08400000
    0.10900000 0.18200000 0.19200000 0.20000000 0.20000000 0.20000000
    0.13900000 0.23000000 0.24600000 0.25600000 0.25700000 0.25800000
    0.35400000 0.47600000 0.50400000 0.52400000 0.52700000 0.52700000
    0.69700000 0.85400000 0.87200000 0.88300000 0.88500000 0.88500000
    0.81500000 0.95000000 0.96500000 0.97500000 0.97500000 0.97500000
    0.89600000 0.98200000 0.98900000 0.99500000 0.99500000 0.99500000
    0.89300000 0.99300000 0.99600000 0.99700000 0.99700000 0.99700000
];

hitLow = [
    0.00054864 0.00054864 0.00054864 0.00155659 0.00155659 0.00155659
    0.00054864 0.00102078 0.00155659 0.00213754 0.00213754 0.00213754
    0.01219689 0.02275711 0.02527226 0.02696118 0.02696118 0.02780900
    0.02026645 0.05132377 0.05756392 0.06835881 0.06835881 0.06835881
    0.09116003 0.15931726 0.16878485 0.17637709 0.17637709 0.17637709
    0.11893639 0.20497969 0.22031215 0.22992018 0.23088202 0.23184403
    0.32497103 0.44519696 0.47305528 0.49301327 0.49601123 0.49601123
    0.66780768 0.83075993 0.84986041 0.86159709 0.86373683 0.86373683
    0.78974395 0.93468618 0.95171338 0.96335471 0.96335471 0.96335471
    0.87554024 0.97172674 0.98041060 0.98834904 0.98834904 0.98834904
    0.87231504 0.98562168 0.98976044 0.99121699 0.99121699 0.99121699
];

hitHigh = [
    0.00726281 0.00726281 0.00726281 0.01023956 0.01023956 0.01023956
    0.00726281 0.00878301 0.01023956 0.01165096 0.01165096 0.01165096
    0.02948446 0.04482474 0.04828662 0.05058240 0.05058240 0.05172692
    0.04133836 0.08200551 0.08971178 0.10282505 0.10282505 0.10282505
    0.12983249 0.20711656 0.21757244 0.22591896 0.22591896 0.22591896
    0.16182653 0.25708676 0.27363184 0.28394727 0.28497779 0.28600812
    0.38414638 0.50698673 0.53491411 0.55480304 0.55778212 0.55778212
    0.72468458 0.87453073 0.89129248 0.90147161 0.90331657 0.90331657
    0.83784520 0.96186974 0.97472774 0.98300987 0.98300987 0.98300987
    0.91342897 0.98858426 0.99384683 0.99786246 0.99786246 0.99786246
    0.91067713 0.99660513 0.99844341 0.99897922 0.99897922 0.99897922
];

mrr = [
    0.00214583 0.00253333 0.02478026 0.04560585 0.14077340 ...
    0.17967671 0.41107116 0.76426976 0.87259350 0.93488963 0.93784167
];
mrrLow = [
    0.00006250 0.00016667 0.01617007 0.03478825 0.12167428 ...
    0.15818095 0.38357865 0.74067536 0.85509005 0.92211311 0.92613313
];
mrrHigh = [
    0.00518802 0.00576667 0.03398337 0.05764907 0.16090268 ...
    0.20148721 0.43949473 0.78764459 0.88953608 0.94690999 0.94910000
];

finalRetention = [
    0.00400000 0.00500000 0.03800000 0.08400000 0.20000000 ...
    0.25800000 0.52700000 0.88500000 0.97500000 0.99500000 0.99700000
];

observedQ1 = [1 1 1 1 1 1 1 1 1 1 1];
observedMedian = [6.5 3 1.5 2 1 1 1 1 1 1 1];
observedQ3 = [13 6 3 5 2 3 2 1 1 1 1];

oracleQ1 = [6 1 1 1 1 1 1 1 1 1 1];
oracleMedian = [100.5 1 1 1 1 1 1 1 1 1 1];
oracleQ3 = [611 5 1 1 1 1 2 1 1 1 1];

scoreGapMean = [
   -0.54233121 0.24986942 0.50236164 0.61908201 0.61194060 ...
    0.60783217 0.34946988 0.10573835 0.06303240 0.05493134 0.04269898
];
scoreGapLow = [
   -0.58136601 0.21979257 0.47007510 0.58469082 0.57425921 ...
    0.56738005 0.31130194 0.08515383 0.05323314 0.05187004 0.03997245
];
scoreGapHigh = [
   -0.50356213 0.27932521 0.53452798 0.65370477 0.65057167 ...
    0.64758701 0.38805915 0.12835176 0.07454325 0.05791124 0.04550632
];

top1Success = [
    0.002 0.002 0.019 0.029 0.109 0.139 0.354 0.697 0.815 0.896 0.893
];
rankingFailure = [
    0.002 0.003 0.019 0.055 0.091 0.119 0.173 0.188 0.160 0.099 0.104
];
visitedThenPruned = zeros(1, 11);
neverVisited = [
    0.996 0.995 0.962 0.916 0.800 0.742 0.473 0.115 0.025 0.005 0.003
];

%% Embedded archive-capacity sensitivity data
% Rows follow archiveLengths; columns follow archiveCapacities.
archiveLengths = [100 150 200 300];
archiveCapacities = [100 500 1000 2000];

archiveHit1 = [
    0.33333333 0.33333333 0.33333333 0.33333333
    0.72333333 0.72333333 0.72333333 0.72333333
    0.82000000 0.82000000 0.82000000 0.82000000
    0.89000000 0.89000000 0.89000000 0.89000000
];
archiveHit1Low = [
    0.28239345 0.28239345 0.28239345 0.28239345
    0.67013006 0.67013006 0.67013006 0.67013006
    0.77256680 0.77256680 0.77256680 0.77256680
    0.84954377 0.84954377 0.84954377 0.84954377
];
archiveHit1High = [
    0.38848754 0.38848754 0.38848754 0.38848754
    0.77088942 0.77088942 0.77088942 0.77088942
    0.85934170 0.85934170 0.85934170 0.85934170
    0.92059471 0.92059471 0.92059471 0.92059471
];

archiveHit10 = [
    0.50666667 0.50666667 0.50666667 0.50666667
    0.87000000 0.87000000 0.87000000 0.87000000
    0.97666667 0.97666667 0.97666667 0.97666667
    0.98666667 0.98666667 0.98666667 0.98666667
];
archiveHit10Low = [
    0.45036683 0.45036683 0.45036683 0.45036683
    0.82721957 0.82721957 0.82721957 0.82721957
    0.95262803 0.95262803 0.95262803 0.95262803
    0.96622447 0.96622447 0.96622447 0.96622447
];
archiveHit10High = [
    0.56279793 0.56279793 0.56279793 0.56279793
    0.90342463 0.90342463 0.90342463 0.90342463
    0.98865234 0.98865234 0.98865234 0.98865234
    0.99480304 0.99480304 0.99480304 0.99480304
];

archiveRetention = [
    0.52666667 0.52666667 0.52666667 0.52666667
    0.88666667 0.88666667 0.88666667 0.88666667
    0.98333333 0.98333333 0.98333333 0.98333333
    0.99666667 0.99666667 0.99666667 0.99666667
];
archiveRetentionLow = [
    0.47018804 0.47018804 0.47018804 0.47018804
    0.84580060 0.84580060 0.84580060 0.84580060
    0.96158461 0.96158461 0.96158461 0.96158461
    0.98136331 0.98136331 0.98136331 0.98136331
];
archiveRetentionHigh = [
    0.58247100 0.58247100 0.58247100 0.58247100
    0.91775550 0.91775550 0.91775550 0.91775550
    0.99286052 0.99286052 0.99286052 0.99286052
    0.99941134 0.99941134 0.99941134 0.99941134
];

%% Data-integrity checks
assert(isequal(size(hitRate), [numel(ciphertextLengths), 6]));
assert(all(hitLow <= hitRate & hitRate <= hitHigh, 'all'));
assert(max(abs(top1Success + rankingFailure + ...
    visitedThenPruned + neverVisited - 1)) < 1e-12);
assert(max(abs(diff(archiveHit1, 1, 2)), [], 'all') < 1e-12);
assert(max(abs(diff(archiveHit10, 1, 2)), [], 'all') < 1e-12);
assert(max(abs(diff(archiveRetention, 1, 2)), [], 'all') < 1e-12);

%% Figure 1: Hit@k versus ciphertext length
fig = figure('Color', 'w', 'Visible', figureVisible, ...
    'Position', [60 40 1320 920]);
layout = tiledlayout(fig, 2, 1, 'TileSpacing', 'compact', 'Padding', 'compact');

ax = nexttile(layout);
drawHitPanel(ax, ciphertextLengths, hitRate, hitLow, hitHigh, ...
    1:3, colors, markers, {'Hit@1', 'Hit@5', 'Hit@10'});
title(ax, '(a) Practical candidate ranges');
xlabel(ax, '');

ax = nexttile(layout);
drawHitPanel(ax, ciphertextLengths, hitRate, hitLow, hitHigh, ...
    4:6, colors, markers, {'Hit@50', 'Hit@100', 'Hit@1000'});
title(ax, '(b) Deeper archive ranges');
xlabel(ax, 'Ciphertext length');

title(layout, 'Top-k recovery across ciphertext lengths (95% Wilson intervals)', ...
    'FontWeight', 'bold', 'FontSize', 15);
exportPaperFigure(fig, outputDir, 'hitk_vs_ciphertext_length', pngResolution);

%% Figure 2: MRR versus ciphertext length
fig = figure('Color', 'w', 'Visible', figureVisible, ...
    'Position', [80 70 1180 680]);
ax = axes(fig);
hold(ax, 'on');
plotBand(ax, 1:numel(ciphertextLengths), mrrLow, mrrHigh, colors(1,:), 0.18);
plot(ax, 1:numel(ciphertextLengths), mrr, '-o', ...
    'Color', colors(1,:), 'MarkerFaceColor', 'w', 'MarkerSize', 7);
formatLengthAxis(ax, ciphertextLengths);
xlabel(ax, 'Ciphertext length');
ylabel(ax, 'Mean reciprocal rank');
ylim(ax, [0 1]);
title(ax, 'Overall ranking quality (95% bootstrap interval)');
grid(ax, 'on');
box(ax, 'on');
exportPaperFigure(fig, outputDir, 'mrr_vs_ciphertext_length', pngResolution);

%% Figure 3: Observed rank versus oracle-score rank
fig = figure('Color', 'w', 'Visible', figureVisible, ...
    'Position', [70 40 1320 880]);
layout = tiledlayout(fig, 2, 1, 'TileSpacing', 'compact', 'Padding', 'compact');

ax = nexttile(layout);
hold(ax, 'on');
errorbar(ax, 1:numel(ciphertextLengths), observedMedian, ...
    observedMedian - observedQ1, observedQ3 - observedMedian, ...
    '-o', 'Color', colors(1,:), 'MarkerFaceColor', 'w', ...
    'MarkerSize', 7, 'CapSize', 7);
errorbar(ax, 1:numel(ciphertextLengths), oracleMedian, ...
    oracleMedian - oracleQ1, oracleQ3 - oracleMedian, ...
    '-s', 'Color', colors(2,:), 'MarkerFaceColor', 'w', ...
    'MarkerSize', 7, 'CapSize', 7);
set(ax, 'YScale', 'log');
formatLengthAxis(ax, ciphertextLengths);
ylabel(ax, 'Rank (median and IQR, log scale)');
ylim(ax, [0.8 1000]);
legend(ax, {'Observed rank | retained trials', 'Oracle-score rank | all trials'}, ...
    'Location', 'northeast');
title(ax, '(a) Conditional observed rank and oracle-score rank');
grid(ax, 'on');
box(ax, 'on');

ax = nexttile(layout);
hold(ax, 'on');
plotBand(ax, 1:numel(ciphertextLengths), hitLow(:,6)', ...
    hitHigh(:,6)', colors(3,:), 0.18);
plot(ax, 1:numel(ciphertextLengths), finalRetention, '-d', ...
    'Color', colors(3,:), 'MarkerFaceColor', 'w', 'MarkerSize', 7);
formatLengthAxis(ax, ciphertextLengths);
xlabel(ax, 'Ciphertext length');
ylabel(ax, 'Final-archive retention');
ylim(ax, [0 1]);
formatProbabilityTicks(ax);
title(ax, '(b) Retention accompanying the conditional observed-rank summary');
grid(ax, 'on');
box(ax, 'on');

title(layout, 'Observed rank versus oracle-score rank', ...
    'FontWeight', 'bold', 'FontSize', 15);
exportPaperFigure(fig, outputDir, 'observed_vs_oracle_rank', pngResolution);

%% Figure 4: Score gap versus ciphertext length
fig = figure('Color', 'w', 'Visible', figureVisible, ...
    'Position', [80 70 1180 680]);
ax = axes(fig);
hold(ax, 'on');
plotBand(ax, 1:numel(ciphertextLengths), scoreGapLow, scoreGapHigh, ...
    colors(2,:), 0.18);
yline(ax, 0, '--', 'Zero preference', 'Color', [0.25 0.25 0.25], ...
    'LabelHorizontalAlignment', 'left');
plot(ax, 1:numel(ciphertextLengths), scoreGapMean, '-s', ...
    'Color', colors(2,:), 'MarkerFaceColor', 'w', 'MarkerSize', 7);
formatLengthAxis(ax, ciphertextLengths);
xlabel(ax, 'Ciphertext length');
ylabel(ax, 'Mean score gap');
title(ax, 'Scoring preference for the correct plaintext (95% bootstrap interval)');
grid(ax, 'on');
box(ax, 'on');
exportPaperFigure(fig, outputDir, 'score_gap_vs_ciphertext_length', pngResolution);

%% Figure 5: Failure-category breakdown
fig = figure('Color', 'w', 'Visible', figureVisible, ...
    'Position', [80 70 1240 720]);
ax = axes(fig);
failureMatrix = 100 * [
    top1Success(:), rankingFailure(:), ...
    visitedThenPruned(:), neverVisited(:)
];
bars = bar(ax, 1:numel(ciphertextLengths), failureMatrix, ...
    'stacked', 'BarWidth', 0.78);
failureColors = [colors(3,:); colors(2,:); colors(5,:); 0.55 0.55 0.55];
for i = 1:numel(bars)
    bars(i).FaceColor = failureColors(i,:);
    bars(i).EdgeColor = 'none';
end
formatLengthAxis(ax, ciphertextLengths);
xlabel(ax, 'Ciphertext length');
ylabel(ax, 'Share of trials (%)');
ylim(ax, [0 100]);
legend(ax, {'Top-1 success', 'Ranking failure', ...
    'Visited then pruned', 'Never visited'}, ...
    'Location', 'eastoutside');
title(ax, 'Failure-category breakdown (n = 1,000 per length)');
text(ax, 0.02, 0.97, 'Visited then pruned: 0 / 11,000 trials', ...
    'Units', 'normalized', 'VerticalAlignment', 'top', ...
    'FontSize', 11, 'Color', [0.25 0.25 0.25]);
grid(ax, 'on');
ax.YGrid = 'on';
ax.XGrid = 'off';
box(ax, 'on');
exportPaperFigure(fig, outputDir, 'failure_category_breakdown', pngResolution);

%% Figure 6: Archive-capacity sensitivity
fig = figure('Color', 'w', 'Visible', figureVisible, ...
    'Position', [40 100 1540 560]);
layout = tiledlayout(fig, 1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');

ax1 = nexttile(layout);
drawArchivePanel(ax1, archiveLengths, archiveCapacities, ...
    archiveHit1, archiveHit1Low, archiveHit1High, ...
    colors, markers, 'Hit@1', [0.25 0.95]);

ax2 = nexttile(layout);
drawArchivePanel(ax2, archiveLengths, archiveCapacities, ...
    archiveHit10, archiveHit10Low, archiveHit10High, ...
    colors, markers, 'Hit@10', [0.42 1.01]);

ax3 = nexttile(layout);
drawArchivePanel(ax3, archiveLengths, archiveCapacities, ...
    archiveRetention, archiveRetentionLow, archiveRetentionHigh, ...
    colors, markers, 'Final-archive retention', [0.42 1.01]);

legend(ax3, compose('K = %d', archiveCapacities), ...
    'Location', 'southoutside', 'NumColumns', 2);
title(layout, ...
    'Archive-capacity sensitivity (n = 300 per setting)', ...
    'FontWeight', 'bold', 'FontSize', 15);
exportPaperFigure(fig, outputDir, 'archive_capacity_sensitivity', pngResolution);

fprintf('Generated six figure pairs in:\\n%s\\n', outputDir);

%% Local helper functions
function drawHitPanel(ax, lengths, estimate, low, high, ...
    columns, colors, markers, labels)
    hold(ax, 'on');
    x = 1:numel(lengths);
    lineHandles = gobjects(1, numel(columns));
    for j = 1:numel(columns)
        c = columns(j);
        plotBand(ax, x, low(:,c)', high(:,c)', colors(j,:), 0.12);
        lineHandles(j) = plot(ax, x, estimate(:,c)', ...
            ['-' markers{j}], 'Color', colors(j,:), ...
            'MarkerFaceColor', 'w', 'MarkerSize', 6.5);
    end
    formatLengthAxis(ax, lengths);
    ylabel(ax, 'Hit probability');
    ylim(ax, [0 1.02]);
    formatProbabilityTicks(ax);
    legend(ax, lineHandles, labels, 'Location', 'southeast', ...
        'NumColumns', numel(columns));
    grid(ax, 'on');
    box(ax, 'on');
end

function drawArchivePanel(ax, lengths, capacities, estimate, low, high, ...
    colors, markers, panelTitle, yLimits)
    hold(ax, 'on');
    x = 1:numel(lengths);
    offsets = linspace(-0.18, 0.18, numel(capacities));
    handles = gobjects(1, numel(capacities));
    for c = 1:numel(capacities)
        xc = x + offsets(c);
        handles(c) = errorbar(ax, xc, estimate(:,c)', ...
            estimate(:,c)' - low(:,c)', high(:,c)' - estimate(:,c)', ...
            ['-' markers{c}], 'Color', colors(c,:), ...
            'MarkerFaceColor', 'w', 'MarkerSize', 6.5, 'CapSize', 5);
    end
    xticks(ax, x);
    xticklabels(ax, string(lengths));
    xlim(ax, [0.55 numel(lengths) + 0.45]);
    xlabel(ax, 'Ciphertext length');
    ylabel(ax, 'Probability');
    ylim(ax, yLimits);
    formatProbabilityTicks(ax);
    title(ax, panelTitle);
    grid(ax, 'on');
    box(ax, 'on');
end

function plotBand(ax, x, low, high, color, alphaValue)
    x = x(:)';
    low = low(:)';
    high = high(:)';
    fill(ax, [x fliplr(x)], [low fliplr(high)], color, ...
        'FaceAlpha', alphaValue, 'EdgeColor', 'none', ...
        'HandleVisibility', 'off');
end

function formatLengthAxis(ax, lengths)
    x = 1:numel(lengths);
    xticks(ax, x);
    xticklabels(ax, string(lengths));
    xlim(ax, [0.65 numel(lengths) + 0.35]);
end

function formatProbabilityTicks(ax)
    ticks = yticks(ax);
    yticklabels(ax, compose('%.0f%%', 100 * ticks));
end

function exportPaperFigure(fig, outputDir, baseName, resolution)
    drawnow;
    pngPath = fullfile(outputDir, [baseName '.png']);
    pdfPath = fullfile(outputDir, [baseName '.pdf']);
    exportgraphics(fig, pngPath, 'Resolution', resolution, ...
        'BackgroundColor', 'white');
    exportgraphics(fig, pdfPath, 'ContentType', 'vector', ...
        'BackgroundColor', 'white');
end
