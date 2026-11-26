












clear;
clc;
close all;

%% Output and visual settings
scriptDir = fileparts(mfilename('fullpath'));
outputDir = fullfile(scriptDir, '..', 'results', 'matlab_paper_figures_revised');
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

%% Embedded reviewer-supplement data
% All settings use n = 500 trials per length. The four lengths were selected
% to cover the short, transition, long, and longest-text regimes.
supplementLengths = [25 100 200 500];

originalTotalProposals = [96846.604 109934.072 116291.130 116895.898];
originalNeutralFraction = [
    0.22145028 0.04131671 0.01919738 0.00806235
];
originalNonNeutralProposals = originalTotalProposals .* ...
    (1 - originalNeutralFraction);
controlledNonNeutralProposals = [120000 120000 120000 120000];

originalHit1 = [0.000 0.328 0.848 0.900];
originalHit1Low = [0.00000000 0.28829619 0.81388585 0.87057809];
originalHit1High = [0.00762434 0.37032658 0.87680761 0.92332244];
controlledHit1 = [0.000 0.308 0.834 0.902];
controlledHit1Low = [0.00000000 0.26912575 0.79886468 0.87279395];
controlledHit1High = [0.00762434 0.34980200 0.86404226 0.92507608];

controlledVisited = [0.008 0.464 0.968 0.998];
controlledVisitedLow = [0.00311532 0.42072819 0.94865513 0.98875929];
controlledVisitedHigh = [0.02038704 0.50782077 0.98020849 0.99964686];
saVisited = [0.022 0.804 0.996 1.000];
saVisitedLow = [0.01232801 0.76694251 0.98553428 0.99237566];
saVisitedHigh = [0.03896086 0.83642189 0.99890237 1.00000000];

saHit1 = [0.002 0.514 0.848 0.904];
saHit1Low = [0.00035314 0.47025151 0.81388585 0.87501304];
saHit1High = [0.01124071 0.55753501 0.87680761 0.92682650];

% Rows are 3-, 4-, and 5-gram rerankers; columns follow supplementLengths.
hcRerankHit1 = [
    0.000 0.152 0.638 0.866
    0.000 0.308 0.834 0.902
    0.000 0.366 0.876 0.930
];
hcRerankLow = [
    0.00000000 0.12319239 0.59497173 0.83333398
    0.00000000 0.26912575 0.79886468 0.87279395
    0.00000000 0.32494760 0.84421259 0.90420281
];
hcRerankHigh = [
    0.00762434 0.18611415 0.67892396 0.89308500
    0.00762434 0.34980200 0.86404226 0.92507608
    0.00762434 0.40909572 0.90205391 0.94924026
];

saRerankHit1 = [
    0.000 0.206 0.644 0.866
    0.002 0.514 0.848 0.904
    0.010 0.612 0.888 0.932
];
saRerankLow = [
    0.00000000 0.17285664 0.60107875 0.83333398
    0.00035314 0.47025151 0.81388585 0.87501304
    0.00427875 0.56858818 0.85734631 0.90647908
];
saRerankHigh = [
    0.00762434 0.24362647 0.68472544 0.89308500
    0.01124071 0.55753501 0.87680761 0.92682650
    0.02319310 0.65370397 0.91273720 0.95093349
];

%% Data-integrity checks
assert(isequal(size(hitRate), [numel(ciphertextLengths), 6]));
assert(all(hitLow <= hitRate & hitRate <= hitHigh, 'all'));
assert(max(abs(top1Success + rankingFailure + ...
    visitedThenPruned + neverVisited - 1)) < 1e-12);
assert(max(abs(diff(archiveHit1, 1, 2)), [], 'all') < 1e-12);
assert(max(abs(diff(archiveHit10, 1, 2)), [], 'all') < 1e-12);
assert(max(abs(diff(archiveRetention, 1, 2)), [], 'all') < 1e-12);
assert(all(originalHit1Low <= originalHit1 & ...
    originalHit1 <= originalHit1High));
assert(all(controlledHit1Low <= controlledHit1 & ...
    controlledHit1 <= controlledHit1High));
assert(all(controlledVisitedLow <= controlledVisited & ...
    controlledVisited <= controlledVisitedHigh));
assert(all(saVisitedLow <= saVisited & saVisited <= saVisitedHigh));
assert(all(saHit1Low <= saHit1 & saHit1 <= saHit1High));
assert(all(hcRerankLow <= hcRerankHit1 & hcRerankHit1 <= hcRerankHigh, 'all'));
assert(all(saRerankLow <= saRerankHit1 & saRerankHit1 <= saRerankHigh, 'all'));

%% Paper Figure 2: Hit@k and MRR versus ciphertext length
fig = figure('Color', 'w', 'Visible', figureVisible, ...
    'Position', [20 100 2460 620]);
layout = tiledlayout(fig, 1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');

ax = nexttile(layout);
drawHitPanel(ax, ciphertextLengths, hitRate, hitLow, hitHigh, ...
    1:3, colors, markers, {'Hit@1', 'Hit@5', 'Hit@10'});
title(ax, '(a) Practical candidate ranges');
xlabel(ax, 'Ciphertext length');

ax = nexttile(layout);
drawHitPanel(ax, ciphertextLengths, hitRate, hitLow, hitHigh, ...
    4:6, colors, markers, {'Hit@50', 'Hit@100', 'Hit@1000'});
title(ax, '(b) Deeper archive ranges');
xlabel(ax, 'Ciphertext length');

ax = nexttile(layout);
hold(ax, 'on');
plotBand(ax, ciphertextLengths, mrrLow, mrrHigh, colors(1,:), 0.18);
plot(ax, ciphertextLengths, mrr, '-o', ...
    'Color', colors(1,:), 'MarkerFaceColor', 'w', 'MarkerSize', 7);
formatNumericLengthAxis(ax, ciphertextLengths);
xlabel(ax, 'Ciphertext length');
ylabel(ax, 'Mean reciprocal rank');
ylim(ax, [0 1]);
title(ax, '(c) Mean reciprocal rank');
grid(ax, 'on');
box(ax, 'on');

title(layout, 'Top-k recovery and ranking quality across ciphertext lengths', ...
    'FontWeight', 'bold', 'FontSize', 15);
exportPaperFigure(fig, outputDir, 'figure2_hitk_and_mrr', pngResolution);

%% Paper Figures 4-5 combined: rank, retention, and score gap
fig = figure('Color', 'w', 'Visible', figureVisible, ...
    'Position', [20 100 2460 620]);
layout = tiledlayout(fig, 1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');

ax = nexttile(layout);
hold(ax, 'on');
errorbar(ax, ciphertextLengths, observedMedian, ...
    observedMedian - observedQ1, observedQ3 - observedMedian, ...
    '-o', 'Color', colors(1,:), 'MarkerFaceColor', 'w', ...
    'MarkerSize', 7, 'CapSize', 7);
errorbar(ax, ciphertextLengths, oracleMedian, ...
    oracleMedian - oracleQ1, oracleQ3 - oracleMedian, ...
    '-s', 'Color', colors(2,:), 'MarkerFaceColor', 'w', ...
    'MarkerSize', 7, 'CapSize', 7);
set(ax, 'YScale', 'log');
formatNumericLengthAxis(ax, ciphertextLengths);
xlabel(ax, 'Ciphertext length');
ylabel(ax, 'Rank (median and IQR, log scale)');
ylim(ax, [0.8 1000]);
legend(ax, {'Observed rank | retained trials', 'Oracle-score rank | all trials'}, ...
    'Location', 'northeast');
title(ax, '(a) Conditional observed rank and oracle-score rank');
grid(ax, 'on');
box(ax, 'on');

ax = nexttile(layout);
hold(ax, 'on');
plotBand(ax, ciphertextLengths, hitLow(:,6)', ...
    hitHigh(:,6)', colors(3,:), 0.18);
plot(ax, ciphertextLengths, finalRetention, '-d', ...
    'Color', colors(3,:), 'MarkerFaceColor', 'w', 'MarkerSize', 7);
formatNumericLengthAxis(ax, ciphertextLengths);
xlabel(ax, 'Ciphertext length');
ylabel(ax, 'Final-archive retention');
ylim(ax, [0 1]);
formatProbabilityTicks(ax);
title(ax, '(b) Retention accompanying the conditional observed-rank summary');
grid(ax, 'on');
box(ax, 'on');

ax = nexttile(layout);
hold(ax, 'on');
plotBand(ax, ciphertextLengths, scoreGapLow, scoreGapHigh, ...
    colors(2,:), 0.18);
yline(ax, 0, '--', 'Zero preference', 'Color', [0.25 0.25 0.25], ...
    'LabelHorizontalAlignment', 'left');
plot(ax, ciphertextLengths, scoreGapMean, '-s', ...
    'Color', colors(2,:), 'MarkerFaceColor', 'w', 'MarkerSize', 7);
formatNumericLengthAxis(ax, ciphertextLengths);
xlabel(ax, 'Ciphertext length');
ylabel(ax, 'Mean score gap');
title(ax, '(c) Correct-plaintext score gap');
grid(ax, 'on');
box(ax, 'on');

title(layout, 'Search retention and ranking diagnostics', ...
    'FontWeight', 'bold', 'FontSize', 15);
exportPaperFigure(fig, outputDir, ...
    'figure4_5_rank_retention_score_gap', pngResolution);

%% Paper Figure 6: Failure-category breakdown
fig = figure('Color', 'w', 'Visible', figureVisible, ...
    'Position', [80 70 1240 720]);
ax = axes(fig);
failureMatrix = 100 * [
    top1Success(:), rankingFailure(:), ...
    visitedThenPruned(:), neverVisited(:)
];
bars = bar(ax, ciphertextLengths, failureMatrix, ...
    'stacked', 'BarWidth', 0.78);
failureColors = [colors(3,:); colors(2,:); colors(5,:); 0.55 0.55 0.55];
for i = 1:numel(bars)
    bars(i).FaceColor = failureColors(i,:);
    bars(i).EdgeColor = 'none';
end
formatNumericLengthAxis(ax, ciphertextLengths);
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

%% Paper Figure 7: Archive-capacity sensitivity
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

%% Combined reviewer-supplement figure: one row, four panels
fig = figure('Color', 'w', 'Visible', figureVisible, ...
    'Position', [10 80 3000 650]);
layout = tiledlayout(fig, 1, 4, 'TileSpacing', 'compact', 'Padding', 'compact');

ax = nexttile(layout);
drawEffortPanel(ax, supplementLengths, originalTotalProposals, ...
    originalNonNeutralProposals, controlledNonNeutralProposals, ...
    originalNeutralFraction, colors, markers);
title(ax, '(a) Realized search effort');

ax = nexttile(layout);
drawTwoSeriesPanel(ax, supplementLengths, originalHit1, controlledHit1, ...
    originalHit1Low, originalHit1High, controlledHit1Low, controlledHit1High, ...
    colors(1:2,:), markers(1:2), {'Original HC', 'Controlled HC'}, ...
    'Hit@1', [0 1]);
formatProbabilityTicks(ax);
title(ax, '(b) Effort-control robustness');

ax = nexttile(layout);
drawSearcherMechanismPanel(ax, supplementLengths, ...
    controlledVisited, controlledVisitedLow, controlledVisitedHigh, ...
    controlledHit1, controlledHit1Low, controlledHit1High, ...
    saVisited, saVisitedLow, saVisitedHigh, ...
    saHit1, saHit1Low, saHit1High, colors(1:2,:));
title(ax, '(c) Search coverage and Hit@1');

ax = nexttile(layout);
drawCombinedRerankPanel(ax, supplementLengths, ...
    hcRerankHit1, hcRerankLow, hcRerankHigh, ...
    saRerankHit1, saRerankLow, saRerankHigh, colors, markers);
title(ax, '(d) Fixed-pool reranking');

title(layout, ...
    'Effort control, alternative search, and fixed-pool reranking (n = 500 per setting)', ...
    'FontWeight', 'bold', 'FontSize', 15);
exportPaperFigure(fig, outputDir, ...
    'reviewer_supplement_combined_single_row', pngResolution);

fprintf('Generated five figure pairs in:\n%s\n', outputDir);

%% Local helper functions
function drawHitPanel(ax, lengths, estimate, low, high, ...
    columns, colors, markers, labels)
    hold(ax, 'on');
    x = lengths;
    lineHandles = gobjects(1, numel(columns));
    for j = 1:numel(columns)
        c = columns(j);
        plotBand(ax, x, low(:,c)', high(:,c)', colors(j,:), 0.12);
        lineHandles(j) = plot(ax, x, estimate(:,c)', ...
            ['-' markers{j}], 'Color', colors(j,:), ...
            'MarkerFaceColor', 'w', 'MarkerSize', 6.5);
    end
    formatNumericLengthAxis(ax, lengths);
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
    x = lengths;
    offsets = linspace(-3, 3, numel(capacities));
    handles = gobjects(1, numel(capacities));
    for c = 1:numel(capacities)
        xc = x + offsets(c);
        handles(c) = errorbar(ax, xc, estimate(:,c)', ...
            estimate(:,c)' - low(:,c)', high(:,c)' - estimate(:,c)', ...
            ['-' markers{c}], 'Color', colors(c,:), ...
            'MarkerFaceColor', 'w', 'MarkerSize', 6.5, 'CapSize', 5);
    end
    formatNumericLengthAxis(ax, lengths);
    xlabel(ax, 'Ciphertext length');
    ylabel(ax, 'Probability');
    ylim(ax, yLimits);
    formatProbabilityTicks(ax);
    title(ax, panelTitle);
    grid(ax, 'on');
    box(ax, 'on');
end

function drawEffortPanel(ax, lengths, originalTotal, originalEffective, ...
    controlledEffective, neutralFraction, colors, markers)
    hold(ax, 'on');
    handles = gobjects(1, 3);
    handles(1) = plot(ax, lengths, originalTotal / 1000, ...
        ['--' markers{3}], 'Color', colors(3,:), ...
        'MarkerFaceColor', 'w', 'MarkerSize', 5.5);
    handles(2) = plot(ax, lengths, originalEffective / 1000, ...
        ['-' markers{1}], 'Color', colors(1,:), ...
        'MarkerFaceColor', 'w', 'MarkerSize', 5.5);
    handles(3) = plot(ax, lengths, controlledEffective / 1000, ...
        ['-' markers{2}], 'Color', colors(2,:), ...
        'MarkerFaceColor', 'w', 'MarkerSize', 5.5);
    for i = 1:numel(lengths)
        text(ax, lengths(i), originalEffective(i) / 1000 - 1.8, ...
            sprintf('%.1f%% neutral', 100 * neutralFraction(i)), ...
            'HorizontalAlignment', 'center', 'VerticalAlignment', 'top', ...
            'FontSize', 8, 'Color', colors(1,:));
    end
    formatNumericLengthAxis(ax, lengths);
    xlabel(ax, 'Ciphertext length');
    ylabel(ax, 'Mean proposals (10^3)');
    ylim(ax, [70 125]);
    legend(ax, handles, {'Original total', 'Original non-neutral', ...
        'Controlled non-neutral'}, 'Location', 'southeast');
    grid(ax, 'on');
    box(ax, 'on');
end

function drawTwoSeriesPanel(ax, lengths, first, second, ...
    firstLow, firstHigh, secondLow, secondHigh, ...
    colors, markers, labels, yLabelText, yLimits)
    hold(ax, 'on');
    handles = gobjects(1, 2);
    values = {first, second};
    lows = {firstLow, secondLow};
    highs = {firstHigh, secondHigh};
    for i = 1:2
        if isempty(lows{i})
            handles(i) = plot(ax, lengths, values{i}, ...
                ['-' markers{i}], 'Color', colors(i,:), ...
                'MarkerFaceColor', 'w', 'MarkerSize', 5.5);
        else
            handles(i) = errorbar(ax, lengths, values{i}, ...
                values{i} - lows{i}, highs{i} - values{i}, ...
                ['-' markers{i}], 'Color', colors(i,:), ...
                'MarkerFaceColor', 'w', 'MarkerSize', 5.5, 'CapSize', 4);
        end
    end
    formatNumericLengthAxis(ax, lengths);
    xlabel(ax, 'Ciphertext length');
    ylabel(ax, yLabelText);
    ylim(ax, yLimits);
    legend(ax, handles, labels, 'Location', 'best');
    grid(ax, 'on');
    box(ax, 'on');
end

function drawSearcherMechanismPanel(ax, lengths, ...
    hcVisited, hcVisitedLow, hcVisitedHigh, ...
    hcHit1, hcHit1Low, hcHit1High, ...
    saVisited, saVisitedLow, saVisitedHigh, ...
    saHit1, saHit1Low, saHit1High, colors)
    hold(ax, 'on');
    handles = gobjects(1, 4);
    handles(1) = errorbar(ax, lengths, hcVisited, ...
        hcVisited - hcVisitedLow, hcVisitedHigh - hcVisited, ...
        '-o', 'Color', colors(1,:), 'MarkerFaceColor', 'w', ...
        'MarkerSize', 5.5, 'CapSize', 4);
    handles(2) = errorbar(ax, lengths, hcHit1, ...
        hcHit1 - hcHit1Low, hcHit1High - hcHit1, ...
        '--s', 'Color', colors(1,:), 'MarkerFaceColor', 'w', ...
        'MarkerSize', 5.5, 'CapSize', 4);
    handles(3) = errorbar(ax, lengths, saVisited, ...
        saVisited - saVisitedLow, saVisitedHigh - saVisited, ...
        '-o', 'Color', colors(2,:), 'MarkerFaceColor', 'w', ...
        'MarkerSize', 5.5, 'CapSize', 4);
    handles(4) = errorbar(ax, lengths, saHit1, ...
        saHit1 - saHit1Low, saHit1High - saHit1, ...
        '--s', 'Color', colors(2,:), 'MarkerFaceColor', 'w', ...
        'MarkerSize', 5.5, 'CapSize', 4);
    formatNumericLengthAxis(ax, lengths);
    xlabel(ax, 'Ciphertext length');
    ylabel(ax, 'Probability');
    ylim(ax, [0 1.02]);
    formatProbabilityTicks(ax);
    legend(ax, handles, {'HC visited', 'HC Hit@1', ...
        'SA visited', 'SA Hit@1'}, 'Location', 'southeast');
    grid(ax, 'on');
    box(ax, 'on');
end

function drawCombinedRerankPanel(ax, lengths, ...
    hcEstimate, hcLow, hcHigh, saEstimate, saLow, saHigh, colors, markers)
    hold(ax, 'on');
    handles = gobjects(1, 6);
    for orderIndex = 1:3
        handles(orderIndex) = errorbar(ax, lengths, hcEstimate(orderIndex,:), ...
            hcEstimate(orderIndex,:) - hcLow(orderIndex,:), ...
            hcHigh(orderIndex,:) - hcEstimate(orderIndex,:), ...
            ['-' markers{orderIndex}], 'Color', colors(orderIndex,:), ...
            'MarkerFaceColor', 'w', 'MarkerSize', 5.5, 'CapSize', 4);
        handles(orderIndex + 3) = errorbar(ax, lengths, saEstimate(orderIndex,:), ...
            saEstimate(orderIndex,:) - saLow(orderIndex,:), ...
            saHigh(orderIndex,:) - saEstimate(orderIndex,:), ...
            ['--' markers{orderIndex}], 'Color', colors(orderIndex,:), ...
            'MarkerFaceColor', colors(orderIndex,:), ...
            'MarkerSize', 5.5, 'CapSize', 4);
    end
    formatNumericLengthAxis(ax, lengths);
    xlabel(ax, 'Ciphertext length');
    ylabel(ax, 'Hit@1');
    ylim(ax, [0 1.02]);
    formatProbabilityTicks(ax);
    legend(ax, handles, {'HC 3-gram', 'HC 4-gram', 'HC 5-gram', ...
        'SA 3-gram', 'SA 4-gram', 'SA 5-gram'}, ...
        'Location', 'southeast', 'NumColumns', 2);
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

function formatNumericLengthAxis(ax, lengths)
    span = max(lengths) - min(lengths);
    padding = max(5, 0.03 * span);
    xticks(ax, lengths);
    xticklabels(ax, string(lengths));
    xlim(ax, [min(lengths) - padding, max(lengths) + padding]);
    if numel(lengths) > 6
        xtickangle(ax, 45);
    end
end

function formatProbabilityTicks(ax)
    ticks = yticks(ax);
    yticklabels(ax, compose('%.0f%%', 100 * ticks));
end

function exportPaperFigure(fig, outputDir, baseName, resolution)
    axesHandles = findall(fig, 'Type', 'axes');
    for i = 1:numel(axesHandles)
        if isprop(axesHandles(i), 'Toolbar') && ~isempty(axesHandles(i).Toolbar)
            axesHandles(i).Toolbar.Visible = 'off';
        end
    end
    drawnow;
    pngPath = fullfile(outputDir, [baseName '.png']);
    pdfPath = fullfile(outputDir, [baseName '.pdf']);
    exportgraphics(fig, pngPath, 'Resolution', resolution, ...
        'BackgroundColor', 'white');
    exportgraphics(fig, pdfPath, 'ContentType', 'vector', ...
        'BackgroundColor', 'white');
end
