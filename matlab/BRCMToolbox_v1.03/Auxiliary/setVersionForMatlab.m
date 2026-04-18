function setVersionForMatlab(m_classfiles,target_release_version)
%SETVERSIONFORMATLAB Sets the version of the BRCM Toolbox to a specific Matlab release.
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
   


% get current matlab relase version
if nargin < 2
    target_release_version = [];
else
   target_release_version = regexpi(target_release_version,'(R\d\d\d\d[a-z])','match');
   target_release_version = target_release_version{1};
end


current_release_version_matlab = regexpi(version,'(R\d\d\d\d[a-z])','match');
current_release_version_matlab = current_release_version_matlab{1};



META_class_support = true;

% check input arguments
if ~(iscellstr(m_classfiles) || ischar(m_classfiles))
    error('setVersionForMatlab:Arguments','Argument 1 is required to be of type string or cellstring.\n');
end

if ~isempty(target_release_version)
    if ~ischar(target_release_version)
        error('setVersionForMatlab:Arguments','Argument 2 is required to be of type string.\n');
    end
    
    % check if version is a correct version tag
    if isempty(regexp(target_release_version,strcat('^',Constants.expr_MATLAB_release,'$'),'match'))
        error('setVersionForMatlab:Arguments','Argument 2 is not a release tag.\nRelease tag convention: R20dd[a-z].\n');
    end
    
    % check if target release version supports OO
    bit_1 = num2str(Constants.release_Matlab_OO>target_release_version);
    bit_2 = num2str(Constants.release_Matlab_OO<target_release_version);
    value = bin2dec(bit_1)-bin2dec(bit_2);
    
    if value > 0
        error('setVersionForMatlab:Arguments','Target version does not support Object orientation.');
    end
    
    % check if target release version supports METACLASS
    bit_1 = num2str(Constants.release_Matlab_METACLASS>target_release_version);
    bit_2 = num2str(Constants.release_Matlab_METACLASS<target_release_version);
    value = bin2dec(bit_1)-bin2dec(bit_2);
    
    if value > 0
        META_class_support = false;
    end
else
    
    % check if current version supports METACLASSES
    % get release tag
    release_version = regexp(current_release_version_matlab,Constants.expr_MATLAB_release,'match');
    
    bit = num2str(Constants.release_Matlab_METACLASS>release_version{1});
    value = bin2dec(bit);
    if value > 0
        META_class_support = false;
    end
end

% check if class files exist
% single file
if ischar(m_classfiles)
    
    % check if it is an m-file
    [~,~,ext] = fileparts(m_classfiles);
    
    if strcmp(ext,'.m')
        
        % check if m-file is in MATLAB search path
        if ~(exist(m_classfiles,'file')  == 2)
            error('setVersionForMatlab:Unknown','Class file ''%s'' does not exist or is not on MATLAB search path.\n',m_classfiles);
        end
        
    else
        error('setVersionForMatlab:Argument','Argument error.\nClass file (M-file string) on the MATLAB search path required.\n');
    end
    
    % convert variable in order to get same type: cellstring
    m_classfiles = {m_classfiles};
    
elseif iscellstr(m_classfiles)
    
    n_filenames = length(m_classfiles);
    
    for i = 1:n_filenames
        
        [~,~,ext] = fileparts(m_classfiles{i});
        
        if strcmp(ext,'.m')
            
            % check if m-file is in MATLAB search path
            if ~(exist(m_classfiles{i},'file')  == 2)
                error('setVersionForMatlab:Unknown','Class file ''%s'' does not exist or is not on MATLAB search path.\n',m_classfiles{i});
            end
            
        else
            error('setVersionForMatlab:Argument','Argument error.\nClass file (M-file string) on the MATLAB search path required.\n');
        end
    end
end

% all provided files are m-files on MATLAB search path
n_files = length(m_classfiles);

for i = 1:n_files
    
    % find file
    path_classfile = which(m_classfiles{i});
    
    % check if is class file: Skip file and issue a warning that is not a
    % class file
    L = getLines(path_classfile);
    
    L_noLeadingSpaces = regexprep(L,'^\s*+',''); % remove leading spaces etc
    L_noLeadingSpacesNoComments = regexprep(L_noLeadingSpaces,'%(.+|)','');
    
    if ~any(strncmp('classdef',L_noLeadingSpacesNoComments,length('classdef')))
        warning('setVersionForMatlab:NotClassFile','File ''%s'' is not a classdef file. Skipping file.\n',m_classfiles{i});
        continue;
    end
    
    L_out = L;
    
    for j=1:length(L)
        
        line = L{j};
        
        % activate METACLASS_SUPPORT and deactivate other if necessary
        if META_class_support && ischar(line)
            
            if ~isempty(regexp(line,Constants.expr_IF_WITH_METACLASS_SUPPORT,'match'))
                
                str = regexp(line,'^\s*%','match');
                if ~isempty(str)
                    line = regexprep(line,'^\s*%',[str{1}(1:end-1),'']);
                end
                
            elseif ~isempty(regexp(line,Constants.expr_IF_NO_METACLASS_SUPPORT,'match'))
                
                if isempty(regexp(line,'^\s*%','match'))
                    str = regexp(line,'^\s*','match');
                    line = regexprep(line,'^\s*',[str{1},'%']);
                end
                
            end
            
            % activate NO_METACLASS_SUPPORT and deactivate other if necessary
        elseif ~META_class_support && ischar(line)
            
            if ~isempty(regexp(line,Constants.expr_IF_WITH_METACLASS_SUPPORT,'match'))

                if isempty(regexp(line,'^\s*%','match'))
                    str = regexp(line,'^\s*','match');
                    line = regexprep(line,'^\s*',[str{1},'%']);
                end
                
            elseif ~isempty(regexp(line,Constants.expr_IF_NO_METACLASS_SUPPORT,'match'))
                
                str = regexp(line,'^\s*%','match');
                if ~isempty(str)
                    line = regexprep(line,'^\s*%',[str{1}(1:end-1),'']);
                end
                
            end
        end
        
        L_out{j} = line;
    end
    
    fid = fopen(m_classfiles{i},'w');
    fprintf(fid,'%s\n',L_out{:});
    fclose(fid);
end

end

