function [prbs_signal] = prbs(N, max, min, T)
    % --- Argument validation and default values ---
    arguments
        N (1,1) {mustBeNumeric}
        max (1,1) {mustBeNumeric}
        min (1,1) {mustBeNumeric} = 0 % Set the default value for min here
        T (1,1) {mustBeNumeric} = 1 
    end
    % ---------------------------------------------
    numPeriods = 1;
    Range = [min, max];
    Band = [0 T];
    
    %% PRBS
    % Generate a longer PRBS
    %extra = 1000; % Add extra samples for randomness
    %start_idx = randi([1, extra+1]);
    %prbs_signal = prbs_full(start_idx:start_idx+N-1);
    %prbs_full = idinput([N+extra, 1, numPeriods], 'prbs', Band, Range);
    
    %% RBS
    prbs_full = idinput([N, 1, numPeriods], 'rbs', Band, Range);
    prbs_signal = prbs_full;
end

