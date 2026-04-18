% BRCM_SETUP Makes minor modifications to the BRCM Toolbox depending on the current Matlab version. Should be run once after the first installation.
% ------------------------------------------------------------------------
% This file is part of the BRCM Toolbox v1.03.
%
% The BRCM Toolbox - Building Resistance-Capacitance Modeling for Model Predictive Control.
% Copyright (C) 2013  Automatic Control Laboratory, ETH Zurich.
% 
% The BRCM Toolbox is free software; you can redistribute it and/or modify
% it under the terms of the GNU General Public License as published by
% the Free Software Foundation, either version 3 of the License, or
% (at your option) any later version.
% 
% The BRCM Toolbox is distributed in the hope that it will be useful,
% but WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
% GNU General Public License for more details.
% 
% You should have received a copy of the GNU General Public License
% along with the BRCM Toolbox.  If not, see <http://www.gnu.org/licenses/>.
%
% For support check www.brcm.ethz.ch.
% ------------------------------------------------------------------------


close all; 
clc;

BRCMRootPath = getBRCMRootPath();
cd(BRCMRootPath);

folderName = BRCMRootPath;
ignoreDirs = {};
ignoreFiles = {};

mFiles = getAllMFiles(folderName,ignoreDirs,ignoreFiles);
inds_classdefFiles = [];


for i=1:length(mFiles)

   mFile = mFiles{i};

   L = getLines(mFile);
   L_noLeadingSpaces = regexprep(L,'^\s*+',''); % remove leading spaces etc

   inds_classdef = find(strncmp('classdef ',L_noLeadingSpaces,length('classdef ')));
   if ~isempty(inds_classdef)
      inds_classdefFiles(end+1) = i;
   end
   
end

fprintf('%s\n%s\n%s\n%s\n%s\n\n',...
   'For a nicer encapsulation we would like to use metaclass structures in order to ',...
   'set class-specific read/write properties of a class. However, these are only ',...
   'supported from Matlab release R2012a (version 7.13). The default installation',...
   'does not use metaclass structures. To improve your experience, this script will',...
   'change the class definitions if your Matlab version allows to use metaclass structures.')

inp = 'x';
while(inp ~= 'y' && inp ~= 'n')
   inp = input('Ok? (y/n)  ','s');
end

if inp == 'y'

   fprintf('Found the following class definition files:\n\n')
   fprintf('%s\n',mFiles{inds_classdefFiles})
   currentMatlabVersion = version;
   fprintf('Setting according to the following Matlab version: %s\n\n',currentMatlabVersion);

   setVersionForMatlab(mFiles(inds_classdefFiles),currentMatlabVersion);
   
end

