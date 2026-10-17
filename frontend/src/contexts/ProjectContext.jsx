import React, { createContext, useContext, useState, useEffect } from 'react';
import { projectService } from '../services/projectService';
import { useAuth } from './AuthContext';

const ProjectContext = createContext(null);

export const ProjectProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [projects, setProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadProjects = async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const list = await projectService.listProjects();
      setProjects(list);
      if (list.length > 0 && !activeProject) {
        setActiveProject(list[0]);
      }
    } catch (err) {
      console.error("Error loading projects:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, [isAuthenticated]);

  return (
    <ProjectContext.Provider value={{ projects, activeProject, setActiveProject, loadProjects, loading }}>
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = () => useContext(ProjectContext);
