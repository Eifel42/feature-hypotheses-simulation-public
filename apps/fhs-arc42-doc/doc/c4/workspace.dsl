workspace "Feature Hypotheses Simulation" "Architecture for quantitative risk assessment in product development" {

    model {
        // --- People ---
        productOwner = person "Product Owner" "Defines feature priorities and analyses backlog risk" "Product Owner"
        riskManager  = person "Financial Risk Manager" "Analyses portfolio-level risk: CVaR, stress tests, budget frontier" "Risk Manager"
        businessStakeholder = person "Business Stakeholder" "Reviews portfolio risk exposure and investment decisions" "Business"

        // --- Our system ---
        fhsSystem = softwareSystem "Feature Hypotheses Simulation (FHS)" "Applies Monte Carlo simulation, VaR, and CVaR to product backlogs. Runs entirely as a Python library inside Jupyter notebooks — no server or API required." {

            // Containers
            jupyterLab = container "Jupyter Lab" "Interactive analysis environment — code, results, and explanations in one document" "Python / JupyterLab" "Analysis Tool" {

                // Reference & Onboarding
                nbREADME  = component "README" "Learning path overview and notebook navigation guide" "Jupyter Notebook" "Reference"
                nbGLOSSARY = component "GLOSSARY" "Domain glossary: business value, VaR, CVaR, simulation terms" "Jupyter Notebook" "Reference"

                // Core track (Product Owner learning path)
                nb01 = component "01 Getting Started" "One feature, 10,000 scenarios, VaR and expected business value" "Jupyter Notebook" "Core"
                nb02 = component "02 Blockchain Case Study" "Three hypotheses, EUR business values, prioritised roadmap" "Jupyter Notebook" "Core"
                nb03 = component "03 Capital Budgeting" "NPV, IRR, multi-year projections for blockchain investment decision" "Jupyter Notebook" "Core"
                nb04 = component "04 Portfolio Advisor" "Backlog ranking, opportunity cost, budget optimisation with risk constraints" "Jupyter Notebook" "Core"
                nb05 = component "05 Risk Dashboard" "Portfolio VaR/CVaR, correlation heatmap, concentration metrics, budget frontier" "Jupyter Notebook" "Core"
                nb06 = component "06 Delivery Risk" "Break-even probability, expected loss, Loss at Risk (LaR 95%), sunk cost at cancellation" "Jupyter Notebook" "Core"
                nb07 = component "07 Executive Decision" "Board-ready synthesis across value, finance, portfolio, risk, and delivery dimensions" "Jupyter Notebook" "Core"

                // Configuration track
                nbCONFIG = component "Config Reference" "All scenario YAML fields documented with examples and validation rules" "Jupyter Notebook" "Config"

                // Tutorial track
                nbT01 = component "T01 Distribution Guide" "Normal, Lognormal, Beta — choosing the right uncertainty model" "Jupyter Notebook" "Tutorial"

                // Advanced track (Financial Risk Manager)
                nbA01 = component "A01 Portfolio Advisor" "7 backlog questions: opportunity cost, ranking, budget optimisation, stress tests, PO report" "Jupyter Notebook" "Advanced"
                nbA02 = component "A02 Portfolio Risk Dashboard" "Portfolio value, VaR/CVaR metrics, stress scenarios, risk contribution, budget frontier" "Jupyter Notebook" "Advanced"
            }

            pythonLibrary = container "FHS Python Library" "Core simulation and risk calculation library — imported directly by notebooks" "Python Package" "Library" {

                // ── C3 High-Level: DDD Layer Components ──
                presentationLayer = component "Presentation Layer" "Notebook facade (load_scenario), FHSDisplay widgets (show.*), Matplotlib/Plotly charts, styling & formatting" "Python / ipywidgets / Matplotlib" "Presentation Layer"
                applicationLayer = component "Application Layer" "AdvancedPortfolioService with 5 sub-facades (risk, delivery, multi_year, decisions, layers), ScenarioService, CaseStudyService, ExportService" "Python" "Application Layer"
                domainLayer = component "Domain Layer" "Feature entity, 20+ value objects (SimulationResult, LossProfile, etc.), ScenarioConfig aggregate, domain events, repository protocols" "Pydantic / Python" "Domain Layer"
                coreServicesLayer = component "Core Domain Services" "Monte Carlo engine, Risk Calculator (VaR/CVaR), Portfolio analysis, Optimization (ILP/SLSQP), Financial Calculator (NPV/IRR), Reporting" "NumPy / SciPy / PuLP" "Core Service"
                infrastructureLayer = component "Infrastructure Layer" "YAML scenario persistence, CSV/JSON portfolio export, version history tracking, simulation defaults" "PyYAML" "Infrastructure Layer"

                group "Presentation Layer" {
                    notebookFacade   = component "Notebook Facade" "load_scenario(), notebook_setup(), config form — single entry point for all notebooks" "Python / ipywidgets" "Presentation Layer"
                    widgetDisplay    = component "Widget Display" "show.* facade: simulation, comparison, risk, portfolio, delivery, capital budgeting widgets" "Python / ipywidgets" "Presentation Layer"
                    charts           = component "Charts" "Fan charts, heatmaps, distribution plots, portfolio charts, risk profiles (Matplotlib/Plotly)" "Matplotlib / Plotly" "Presentation Layer"
                    styling          = component "Styling & Formatting" "COLORS palette, setup_style(), formatters, HTML template engine" "Python" "Presentation Layer"
                }

                group "Application Layer" {
                    scenarioService  = component "Scenario Service" "Loads, validates, and assembles scenario context via load_scenario()" "Python" "Application Layer"
                    advPortfolio     = component "AdvancedPortfolioService" "Main orchestration facade — delegates to domain sub-facades" "Python" "Application Layer"
                    riskOps          = component "Risk Operations" "service.risk.* — loss metrics, Shapley attribution, component risk" "Python" "Application Layer"
                    deliveryOps      = component "Delivery Operations" "service.delivery.* — delivery risk, sprint overruns, profitability" "Python" "Application Layer"
                    multiYearOps     = component "Multi-Year Operations" "service.multi_year.* — NPV/IRR, multi-year P&L, financial views" "Python" "Application Layer"
                    decisionOps      = component "Decision Operations" "service.decisions.* — feature ranking, score analysis, strategy categories" "Python" "Application Layer"
                    layerOps         = component "Risk Layer Operations" "service.layers.* — risk layer simulation, sensitivity, retention" "Python" "Application Layer"
                    caseStudyService = component "Case Study Service" "Blockchain case study orchestration and board recommendations" "Python" "Application Layer"
                    exportService    = component "Export Service" "Export results to CSV/JSON for portfolio analysis" "Python" "Application Layer"
                    serviceFactory   = component "Service Factory" "Factory pattern for creating and wiring application services" "Python" "Application Layer"
                }

                group "Domain Layer" {
                    domainModels     = component "Domain Models" "Feature entity, SimulationResult, MultiYearResult, BudgetFrontier, value objects" "Pydantic / Python" "Domain Layer"
                    domainEvents     = component "Domain Events" "ScenarioConfigurationChanged, EventBus, EventLogger" "Python" "Domain Layer"
                    domainConfig     = component "Scenario Config" "ScenarioConfig aggregate, DeliveryRiskConfig" "Pydantic" "Domain Layer"
                    repositories     = component "Repository Interfaces" "FeatureRepository protocol — implemented in infrastructure" "Python Protocol" "Domain Layer"
                    exceptions       = component "Domain Exceptions" "FHSException, SimulationError, ValidationError, PortfolioOptimizationError" "Python" "Domain Layer"
                }

                group "Core Domain Services" {
                    monteCarloEngine = component "Monte Carlo Engine" "Scenario generation: Normal, Lognormal, Beta, bounded sampling, correlated draws" "Python / NumPy" "Core Service"
                    riskCalculator   = component "Risk Calculator" "VaR, CVaR, percentiles, confidence intervals, bootstrap, Shapley attribution" "NumPy / SciPy" "Core Service"
                    portfolioService = component "Portfolio Service" "Portfolio VaR/CVaR, correlation matrix, stress testing, budget frontier (ILP/SLSQP)" "NumPy / SciPy" "Core Service"
                    optimizationSvc  = component "Optimization Service" "ILP, CVaR-MILP, and greedy budget optimisation solvers" "Python / SciPy / PuLP" "Core Service"
                    simulationEngine = component "Simulation Engine" "FeatureSimulator orchestration, multi-year simulation, multi-year P&L" "Python / NumPy" "Core Service"
                    assessmentSvc    = component "Assessment & Ranking" "FeatureAssessmentService, RankingService (Expected Value, VaR, CVaR, ROI strategies)" "Python" "Core Service"
                    financialCalc    = component "Financial Calculator" "Present value, NPV, IRR, annualisation computations" "Python" "Core Service"
                    reportingSvc     = component "Reporting Service" "Executive summaries, stress test reports, PO summaries, Year 1 risk reports" "Python" "Core Service"
                }

                group "Infrastructure Layer" {
                    yamlRepository   = component "YAML Repository" "Loads and persists scenario YAML files from notebooks/config/" "PyYAML" "Infrastructure Layer"
                    exporters        = component "Portfolio Exporter" "CSV/JSON export for portfolio optimization results and forecasts" "Python" "Infrastructure Layer"
                    versioningSvc    = component "Versioning Service" "Scenario version history tracking and rollback" "Python" "Infrastructure Layer"
                    infraConfig      = component "Simulation Config" "DEFAULT_CONFIG, logging configuration, validation defaults" "Python" "Infrastructure Layer"
                }
            }
        }

        // --- System Context relationships ---
        productOwner        -> fhsSystem "Analyses feature risk, prioritises backlog"
        riskManager         -> fhsSystem "Reviews portfolio CVaR, stress tests, budget frontier"
        businessStakeholder -> fhsSystem "Reviews quantified risk exposure and EUR figures"

        // --- Container relationships ---
        productOwner        -> jupyterLab "Opens and runs core and tutorial notebooks"
        riskManager         -> jupyterLab "Opens and runs advanced portfolio notebooks"
        businessStakeholder -> jupyterLab "Reviews exported notebook reports"
        jupyterLab          -> pythonLibrary "Uses documented facades/ports (Notebook + Application Layer)"

        // --- Notebook → Presentation Layer (key entry points per track) ---
        nb01  -> notebookFacade "load_scenario()"
        nb02  -> notebookFacade "load_scenario(editable=True)"
        nb03  -> notebookFacade "load_scenario()"
        nb04  -> notebookFacade "load_scenario()"
        nb05  -> notebookFacade "load_scenario()"
        nb06  -> notebookFacade "load_scenario()"
        nb07  -> notebookFacade "load_scenario()"
        nbT01 -> notebookFacade "load_scenario()"
        nbA01 -> notebookFacade "load_scenario()"
        nbA02 -> notebookFacade "load_scenario()"
        nb01  -> widgetDisplay "show.simulation()"
        nb02  -> widgetDisplay "show.simulation(), show.comparison()"
        nb03  -> widgetDisplay "show.multi_year(), show.capital_budgeting()"
        nb04  -> widgetDisplay "show.portfolio_advisor(), show.ranking()"
        nb05  -> widgetDisplay "show.risk_dashboard(), show.budget_frontier()"
        nb06  -> widgetDisplay "show.delivery_risk(), show.break_even()"
        nb07  -> widgetDisplay "show.simulation(), show.capital_budgeting(), show.portfolio_advisor(), show.risk_dashboard(), show.delivery_risk()"
        nbT01 -> widgetDisplay "show.distribution_guide()"
        nbA01 -> widgetDisplay "show.portfolio_advisor()"
        nbA02 -> widgetDisplay "show.risk_dashboard()"

        // --- Presentation Layer internal ---
        notebookFacade -> scenarioService  "load_scenario() — loads and validates config"
        notebookFacade -> widgetDisplay    "delegates show.* rendering"
        widgetDisplay  -> charts           "renders Matplotlib/Plotly figures"
        widgetDisplay  -> styling          "applies COLORS, formatters, templates"
        charts         -> styling          "uses palette, figure sizes"

        // --- Presentation → Application ---
        widgetDisplay  -> advPortfolio     "delegates portfolio analysis"
        charts         -> scenarioService  "delegates single-feature simulations"

        // --- Application → Application (orchestration) ---
        serviceFactory   -> advPortfolio     "creates and wires"
        serviceFactory   -> scenarioService  "creates and wires"
        advPortfolio     -> riskOps          "service.risk.*"
        advPortfolio     -> deliveryOps      "service.delivery.*"
        advPortfolio     -> multiYearOps     "service.multi_year.*"
        advPortfolio     -> decisionOps      "service.decisions.*"
        advPortfolio     -> layerOps         "service.layers.*"
        caseStudyService -> advPortfolio     "orchestrates case study"
        exportService    -> exporters        "delegates CSV/JSON generation"

        // --- Application → Core Services ---
        scenarioService  -> yamlRepository   "loads YAML scenario files"
        scenarioService  -> domainEvents     "publishes ScenarioConfigurationChanged"
        riskOps          -> riskCalculator   "VaR, CVaR, Shapley"
        riskOps          -> portfolioService "portfolio-level risk"
        deliveryOps      -> monteCarloEngine "delivery scenario draws"
        deliveryOps      -> riskCalculator   "loss metrics, LaR"
        multiYearOps     -> monteCarloEngine "multi-year scenario draws"
        multiYearOps     -> financialCalc    "NPV, IRR computations"
        decisionOps      -> optimizationSvc  "budget optimisation"
        decisionOps      -> riskCalculator   "ranking metrics"
        decisionOps      -> assessmentSvc    "feature scoring"
        layerOps         -> portfolioService "portfolio layer analysis"
        reportingSvc     -> riskCalculator   "risk metrics for reports"
        reportingSvc     -> portfolioService "portfolio data for summaries"

        // --- Core service dependencies ---
        monteCarloEngine -> domainModels     "reads Feature parameters"
        riskCalculator   -> domainModels     "reads SimulationResult arrays"
        simulationEngine -> monteCarloEngine "orchestrates scenario draws"
        simulationEngine -> riskCalculator   "calculates result metrics"
        portfolioService -> monteCarloEngine "per-feature simulations"
        portfolioService -> riskCalculator   "portfolio-level risk metrics"
        optimizationSvc  -> portfolioService "feature subset evaluation"
        assessmentSvc    -> riskCalculator   "feature-level risk metrics"
        financialCalc    -> domainModels     "reads Feature financial params"

        // --- Infrastructure ---
        yamlRepository   -> domainModels     "materialises Feature and ScenarioConfig"
        yamlRepository   -> domainConfig     "loads DeliveryRiskConfig"
        versioningSvc    -> yamlRepository   "reads/writes version snapshots"

        // --- High-Level Layer relationships (C3 overview) ---
        jupyterLab          -> presentationLayer   "load_scenario(), show.*()"
        presentationLayer   -> applicationLayer    "delegates analysis & orchestration"
        applicationLayer    -> coreServicesLayer   "simulation, risk, portfolio calculations"
        applicationLayer    -> domainLayer         "reads/creates domain objects"
        coreServicesLayer   -> domainLayer         "operates on Feature, SimulationResult"
        infrastructureLayer -> domainLayer         "materialises entities from YAML"
        applicationLayer    -> infrastructureLayer "loads config, exports results"

        // ---- Deployment Environments ----

        // Option 1: Lima VM Development Sandbox (recommended for macOS)
        deploymentEnvironment "Lima VM (macOS)" {
            limaLaptop = deploymentNode "Developer Laptop" "macOS 14+ (Intel or Apple Silicon)" "macOS" {
                limaHypervisor = deploymentNode "Lima Hypervisor" "Lightweight Linux VM manager" "Lima / QEMU" {
                    limaVM = deploymentNode "fhs VM" "Ubuntu 24.04 · 4 CPUs · 8 GiB RAM · 20 GiB disk" "Ubuntu 24.04 LTS" {
                        limaPythonRT = deploymentNode "Python 3.14 Runtime" "Managed by uv package manager" "Python 3.14 / uv" {
                            limaJupyterInst = containerInstance jupyterLab
                            limaFhsLibInst  = containerInstance pythonLibrary
                        }
                        limaDocsSrv = deploymentNode "Documentation Server" "On-demand documentation build" "docToolchain 3.4.1 / JDK 21 / Gradle 8.5" {
                            // Renders arc42 HTML docs — port 28085 (forwarded from VM to host)
                        }
                    }
                }
                limaBrowser = deploymentNode "Web Browser" "Accesses JupyterLab via port-forwarded localhost:28888" "Chrome / Firefox / Safari" {
                    // Lima port-forwards VM port 8888 → host localhost:28888
                }
                limaIDE = deploymentNode "IDE / Editor" "Remote development via SSH tunnel" "VS Code Remote-SSH / JetBrains Gateway" {
                    // Connects to lima-fhs; full Python toolchain available inside the VM
                }
            }
        }

        // Option 2: Docker quick start
        deploymentEnvironment "Docker" {
            dockerMachine = deploymentNode "Developer Machine" "Any OS with Docker Engine or Docker Desktop" "Linux / macOS / Windows" {
                dockerEngine = deploymentNode "Docker Engine" "" "Docker Engine / Docker Desktop" {
                    dockerContainer = deploymentNode "fhs-platform container" "Python 3.14-slim base image · all dependencies pre-installed" "Docker Container" {
                        dockerPythonRT = deploymentNode "Python 3.14 Runtime" "" "Python 3.14" {
                            dockerJupyterInst = containerInstance jupyterLab
                            dockerFhsLibInst  = containerInstance pythonLibrary
                        }
                    }
                }
                dockerBrowser = deploymentNode "Web Browser" "Accesses JupyterLab at localhost:8888" "Chrome / Firefox / Safari" {
                    // Docker maps container port 8888 → host port 8888
                }
            }
        }

    }

    views {
        // Level 1 — System Context
        systemContext fhsSystem "SystemContext" {
            include productOwner riskManager businessStakeholder
            include fhsSystem
            title "FHS — System Context"
            description "The three primary users and how they interact with the platform"
            autoLayout tb 150 250
        }

        // Level 2 — Containers
        container fhsSystem "Containers" {
            include *
            title "FHS — Container View"
            description "Two containers: Jupyter Lab (all notebooks) and FHS Python Library (DDD layered logic). No server, no API."
            autoLayout tb
        }

        // Level 3 — High-Level Library Architecture (DDD Layers)
        component pythonLibrary "LibraryHighLevel" {
            include presentationLayer applicationLayer domainLayer coreServicesLayer infrastructureLayer
            include jupyterLab
            title "FHS Python Library — DDD Architecture Overview"
            description "Five DDD layers: Presentation → Application → Domain / Core Services ← Infrastructure. Each layer is detailed in a separate zoom-in diagram."
            autoLayout tb
        }

        // Level 3a — Jupyter notebooks grouped by track
        component jupyterLab "JupyterNotebooks" {
            include element.parent==jupyterLab
            title "Jupyter Lab — All Notebooks by Track"
            description "Grey = Reference, Green = Core (PO learning path), Teal = Config, Amber = Tutorial, Blue = Advanced (Risk Manager)"
            autoLayout lr
        }

        // Level 3b — Python library internals
        component pythonLibrary "PythonLibraryComponents" {
            include element.parent==pythonLibrary
            title "FHS Python Library — DDD Layered Components"
            description "Presentation → Application → Domain / Core Services → Infrastructure"
            autoLayout lr
        }

        // Level 3b (focused) — Ports/Facades in one container
        component pythonLibrary "PortsAndFacades" {
            include notebookFacade widgetDisplay scenarioService advPortfolio
            include riskOps deliveryOps multiYearOps decisionOps layerOps
            include simulationEngine portfolioService riskCalculator yamlRepository domainModels
            title "FHS Python Library — Ports & Facades (Application-Layer Centric)"
            description "Primary ports are facades in Presentation/Application. Core and Infrastructure are reached via orchestration, not direct container coupling."
            autoLayout lr
        }

        // Level 3c — Per-layer detail views (progressive zoom)
        component pythonLibrary "PresentationLayer" {
            include notebookFacade widgetDisplay charts styling
            include scenarioService advPortfolio simulationEngine
            title "Presentation Layer — Notebook Facade & Widgets"
            description "Entry points for notebooks: load_scenario(), show.* widgets, charts, styling. Delegates to Application Layer."
            autoLayout lr
        }

        component pythonLibrary "ApplicationLayer" {
            include scenarioService advPortfolio riskOps deliveryOps multiYearOps decisionOps layerOps caseStudyService exportService serviceFactory
            title "Application Layer — Service Orchestration"
            description "AdvancedPortfolioService and its five sub-facades orchestrate domain services. ScenarioService manages YAML loading and validation."
            autoLayout tb
        }

        component pythonLibrary "DomainLayer" {
            include domainModels domainEvents domainConfig repositories exceptions
            include monteCarloEngine riskCalculator simulationEngine yamlRepository
            title "Domain Layer — Entities, Value Objects & Events"
            description "Feature entity, SimulationResult, ScenarioConfig, domain events, repository protocols. Pure domain logic with no infrastructure dependencies."
            autoLayout lr
        }

        component pythonLibrary "CoreServiceLayer" {
            include monteCarloEngine riskCalculator portfolioService optimizationSvc simulationEngine assessmentSvc financialCalc reportingSvc
            title "Core Domain Services — Simulation, Risk & Portfolio"
            description "Monte Carlo engine, risk calculator, portfolio analysis, optimisation solvers, financial computations. Stateless services operating on domain models."
            autoLayout tb
        }

        component pythonLibrary "InfrastructureLayer" {
            include yamlRepository exporters versioningSvc infraConfig
            title "Infrastructure Layer — Persistence & Configuration"
            description "YAML repository, CSV/JSON exporters, versioning, simulation defaults. Implements domain repository protocols."
            autoLayout lr
        }

        // Deployment views — one per environment
        deployment fhsSystem "Lima VM (macOS)" "LimaVMDeployment" {
            include limaLaptop
            title "FHS — Deployment: Lima VM Development Sandbox (macOS)"
            description "Lima-managed Ubuntu 24.04 VM hosts JupyterLab and the FHS Python Library. IDEs connect via SSH; browsers access Jupyter via port-forwarded localhost:28888. Recommended for macOS developers."
            autoLayout tb
        }

        deployment fhsSystem "Docker" "DockerDeployment" {
            include dockerMachine
            title "FHS — Deployment: Docker (Quick Start)"
            description "Single fhs-platform container provides a pre-configured JupyterLab + FHS Library environment. Accessible at localhost:8888. No local Python installation required."
            autoLayout tb
        }

        // Dynamic — typical PO workflow
        dynamic fhsSystem "SimpleFeatureAnalysis" "Typical Product Owner Workflow" {
            productOwner -> jupyterLab    "1. Open notebook, define Feature"
            jupyterLab   -> pythonLibrary "2. load_scenario() + show.simulation()"
            pythonLibrary -> jupyterLab   "3. Return SimulationResult"
            jupyterLab   -> productOwner  "4. Display VaR, expected business value (EUR)"
            title "Typical Product Owner Workflow"
            description "From feature parameters to risk numbers — entirely local, no network calls"
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
                background #08427b
                stroke #052e56
                color #ffffff
                fontSize 20
                metadata true
            }
            element "Risk Manager" {
                shape Person
                background #1b6b3a
                stroke #0f4526
                color #ffffff
                fontSize 20
                metadata true
            }
            element "Business" {
                shape Person
                background #6b4c1b
                stroke #4a3312
                color #ffffff
                fontSize 20
                metadata true
            }
            element "Software System" {
                background #1168bd
                stroke #0b4884
                color #ffffff
                fontSize 22
                shape RoundedBox
                metadata true
            }
            element "Container" {
                background #438dd5
                stroke #2e7cb8
                color #ffffff
                fontSize 18
                shape RoundedBox
                metadata true
            }
            element "Analysis Tool" {
                background #2d7d9a
                stroke #1e5c72
                color #ffffff
                fontSize 18
                shape RoundedBox
                metadata true
            }
            element "Library" {
                background #85bbf0
                stroke #5a9bd4
                color #000000
                fontSize 18
                shape RoundedBox
                metadata true
            }
            element "Component" {
                background #85bbf0
                stroke #5a9bd4
                color #000000
                fontSize 16
                shape RoundedBox
                metadata true
            }
            element "Reference" {
                background #6b6b6b
                stroke #4a4a4a
                color #ffffff
                fontSize 16
                shape RoundedBox
                metadata true
            }
            element "Core" {
                background #1b6b3a
                stroke #0f4526
                color #ffffff
                fontSize 16
                shape RoundedBox
                metadata true
            }
            element "Config" {
                background #2d7d9a
                stroke #1e5c72
                color #ffffff
                fontSize 16
                shape RoundedBox
                metadata true
            }
            element "Tutorial" {
                background #8b5e1a
                stroke #6a4712
                color #ffffff
                fontSize 16
                shape RoundedBox
                metadata true
            }
            element "Advanced" {
                background #08427b
                stroke #052e56
                color #ffffff
                fontSize 16
                shape RoundedBox
                metadata true
            }
            element "Domain Layer" {
                background #e8d5f5
                stroke #9b59b6
                color #000000
                fontSize 15
                shape RoundedBox
                metadata true
            }
            element "Application Layer" {
                background #d5eaf5
                stroke #2980b9
                color #000000
                fontSize 15
                shape RoundedBox
                metadata true
            }
            element "Core Service" {
                background #d5f5e3
                stroke #27ae60
                color #000000
                fontSize 15
                shape RoundedBox
                metadata true
            }
            element "Infrastructure Layer" {
                background #fdebd0
                stroke #e67e22
                color #000000
                fontSize 15
                shape RoundedBox
                metadata true
            }
            element "Presentation Layer" {
                background #f9ebea
                stroke #e74c3c
                color #000000
                fontSize 15
                shape RoundedBox
                metadata true
            }
            relationship "Relationship" {
                thickness 2
                color #707070
                dashed false
                routing Orthogonal
                fontSize 13
                width 250
                position 50
                opacity 100
            }
        }
    }
}
