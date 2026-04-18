function Tamb = sine_Tamb(n_timeSteps, Ts_hrs, mu, A0, K, sigma, seed)
% mu    : mean temperature (degC)
% A0    : amplitude of 24h fundamental (degC)
% K     : number of added harmonics (use 5)
% sigma : std dev of harmonic amplitudes ~ N(0, sigma^2)
% seed  : RNG seed for reproducibility (set [] to skip)

    if ~isempty(seed), rng(seed); end          % reproducible results [optional]
    t_hours = (0:n_timeSteps-1) * Ts_hrs;      % time in hours at simulation grid
    w0 = 2*pi/24;                              % fundamental angular freq (rad/hour)
    Tamb = mu + A0 * sin(w0 * t_hours);        % 24h fundamental

    Ahar = sigma * randn(1, K);                % harmonic amplitudes ~ N(0, sigma^2)
    for k = 1:K
        Tamb = Tamb + Ahar(k) * sin((k+1)*w0 * t_hours); % harmonics 2..K+1
    end
end

