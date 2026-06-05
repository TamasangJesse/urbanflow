pipeline {
    agent any

    environment {
        ROOT_ENV                 = credentials('root-env')
        USER_SERVICE_ENV         = credentials('user-service-env')
        INCIDENT_SERVICE_ENV     = credentials('incident-report-service-env')
        NOTIFICATION_SERVICE_ENV = credentials('notification-service-env')
        TRAFFIC_SERVICE_ENV      = credentials('traffic-intelligence-service-env')
        API_GATEWAY_ENV          = credentials('api-gateway-env')
        RAG_SERVICE_ENV          = credentials('rag-service-env')
        FRONTEND_ENV             = credentials('frontend-env')
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Pulling latest code from GitHub...'
                checkout scm
            }
        }

        stage('Prepare Env Files') {
            steps {
                sh 'cp $ROOT_ENV .env'
                sh 'cp $USER_SERVICE_ENV services/user-service/.env'
                sh 'cp $INCIDENT_SERVICE_ENV services/incident-report-service/.env'
                sh 'cp $NOTIFICATION_SERVICE_ENV services/notification-service/.env'
                sh 'cp $TRAFFIC_SERVICE_ENV services/traffic-intelligence-service/.env'
                sh 'cp $API_GATEWAY_ENV services/api-gateway/.env'
                sh 'cp $RAG_SERVICE_ENV services/rag-service/.env'
                sh 'cp $FRONTEND_ENV frontend/.env'
            }
        }

        stage('Build') {
            steps {
                echo 'Building all Docker images...'
                sh '''
                    set -a && source .env && set +a
                    docker compose -p urbanflow build
                '''
            }
        }

        stage('Test') {
            parallel {
                stage('Test: user-service') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose -p urbanflow run --rm --no-deps -d user-service sleep 60)
                            docker exec -e COVERAGE_FILE=/tmp/.coverage $CONTAINER python -m pytest -v \
                                --junitxml=/tmp/results.xml \
                                --cov=app \
                                --cov-report=xml:/tmp/coverage.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/user-service/tests/results.xml || true
                            docker cp $CONTAINER:/tmp/coverage.xml ${WORKSPACE}/services/user-service/tests/coverage.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/user-service/tests/results.xml'
                            recordCoverage(
                                id: 'user-service',
                                name: 'User Service Coverage',
                                sourceCodeRetention: 'NEVER',
                                tools: [[parser: 'COBERTURA', pattern: 'services/user-service/tests/coverage.xml']]
                            )
                        }
                    }
                }

                stage('Test: incident-report-service') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose -p urbanflow run --rm --no-deps -d incident-report-service sleep 60)
                            docker exec -e COVERAGE_FILE=/tmp/.coverage $CONTAINER python -m pytest -v \
                                --junitxml=/tmp/results.xml \
                                --cov=app \
                                --cov-report=xml:/tmp/coverage.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/incident-report-service/tests/results.xml || true
                            docker cp $CONTAINER:/tmp/coverage.xml ${WORKSPACE}/services/incident-report-service/tests/coverage.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/incident-report-service/tests/results.xml'
                            recordCoverage(
                                id: 'incident-service',
                                name: 'Incident Service Coverage',
                                sourceCodeRetention: 'NEVER',
                                tools: [[parser: 'COBERTURA', pattern: 'services/incident-report-service/tests/coverage.xml']]
                            )
                        }
                    }
                }

                stage('Test: notification-service') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose -p urbanflow run --rm --no-deps -d notification-service sleep 60)
                            docker exec -e COVERAGE_FILE=/tmp/.coverage $CONTAINER python -m pytest -v \
                                --junitxml=/tmp/results.xml \
                                --cov=app \
                                --cov-report=xml:/tmp/coverage.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/notification-service/tests/results.xml || true
                            docker cp $CONTAINER:/tmp/coverage.xml ${WORKSPACE}/services/notification-service/tests/coverage.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/notification-service/tests/results.xml'
                            recordCoverage(
                                id: 'notification-service',
                                name: 'Notification Service Coverage',
                                sourceCodeRetention: 'NEVER',
                                tools: [[parser: 'COBERTURA', pattern: 'services/notification-service/tests/coverage.xml']]
                            )
                        }
                    }
                }

                stage('Test: traffic-intelligence-service') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose -p urbanflow run --rm --no-deps -d traffic-intelligence-service sleep 60)
                            docker exec -e COVERAGE_FILE=/tmp/.coverage $CONTAINER python -m pytest -v \
                                --junitxml=/tmp/results.xml \
                                --cov=app \
                                --cov-report=xml:/tmp/coverage.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/traffic-intelligence-service/tests/results.xml || true
                            docker cp $CONTAINER:/tmp/coverage.xml ${WORKSPACE}/services/traffic-intelligence-service/tests/coverage.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/traffic-intelligence-service/tests/results.xml'
                            recordCoverage(
                                id: 'traffic-service',
                                name: 'Traffic Intelligence Service Coverage',
                                sourceCodeRetention: 'NEVER',
                                tools: [[parser: 'COBERTURA', pattern: 'services/traffic-intelligence-service/tests/coverage.xml']]
                            )
                        }
                    }
                }

                stage('Test: api-gateway') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose -p urbanflow run --rm --no-deps -d api-gateway sleep 60)
                            docker exec -e COVERAGE_FILE=/tmp/.coverage $CONTAINER python -m pytest -v \
                                --junitxml=/tmp/results.xml \
                                --cov=app \
                                --cov-report=xml:/tmp/coverage.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/api-gateway/tests/results.xml || true
                            docker cp $CONTAINER:/tmp/coverage.xml ${WORKSPACE}/services/api-gateway/tests/coverage.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/api-gateway/tests/results.xml'
                            recordCoverage(
                                id: 'api-gateway',
                                name: 'API Gateway Coverage',
                                sourceCodeRetention: 'NEVER',
                                tools: [[parser: 'COBERTURA', pattern: 'services/api-gateway/tests/coverage.xml']]
                            )
                        }
                    }
                }

                stage('Test: rag-service') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose -p urbanflow run --rm --no-deps -d rag-service sleep 60)
                            docker exec -e COVERAGE_FILE=/tmp/.coverage $CONTAINER python -m pytest -v \
                                --junitxml=/tmp/results.xml \
                                --cov=app \
                                --cov-report=xml:/tmp/coverage.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/rag-service/tests/results.xml || true
                            docker cp $CONTAINER:/tmp/coverage.xml ${WORKSPACE}/services/rag-service/tests/coverage.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/rag-service/tests/results.xml'
                            recordCoverage(
                                id: 'rag-service',
                                name: 'RAG Service Coverage',
                                sourceCodeRetention: 'NEVER',
                                tools: [[parser: 'COBERTURA', pattern: 'services/rag-service/tests/coverage.xml']]
                            )
                        }
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying UrbanFlow to Kubernetes...'
                sh '''
                    docker build -t urbanflow-api-gateway:latest ./services/api-gateway
                    docker save urbanflow-api-gateway:latest | /usr/local/bin/k3s ctr images import -

                    docker build -t urbanflow-user-service:latest ./services/user-service
                    docker save urbanflow-user-service:latest | /usr/local/bin/k3s ctr images import -

                    docker build -t urbanflow-incident-report-service:latest ./services/incident-report-service
                    docker save urbanflow-incident-report-service:latest | /usr/local/bin/k3s ctr images import -

                    docker build -t urbanflow-notification-service:latest ./services/notification-service
                    docker save urbanflow-notification-service:latest | /usr/local/bin/k3s ctr images import -

                    docker build -t urbanflow-traffic-intelligence-service:latest ./services/traffic-intelligence-service
                    docker save urbanflow-traffic-intelligence-service:latest | /usr/local/bin/k3s ctr images import -

                    docker build -t urbanflow-rag-service:latest ./services/rag-service
                    docker save urbanflow-rag-service:latest | /usr/local/bin/k3s ctr images import -

                    docker build \
                        --build-arg VITE_API_BASE_URL=https://urbanflow.duckdns.org/api \
                        --build-arg VITE_GOOGLE_MAPS_API_KEY=$(grep VITE_GOOGLE_MAPS_API_KEY frontend/.env | cut -d= -f2) \
                        -t urbanflow-frontend:latest ./frontend
                    docker save urbanflow-frontend:latest | /usr/local/bin/k3s ctr images import -

                    KUBECONFIG=/etc/rancher/k3s/k3s.yaml /usr/local/bin/k3s kubectl \
                      --server=https://194.163.153.164:6443 \
                      --insecure-skip-tls-verify \
                       rollout restart deployment -n urbanflow
                '''
            }
        }
    }

    post {
        always {
            echo "Pipeline finished on branch: ${env.BRANCH_NAME}"
        }
        success {
            echo 'UrbanFlow deployed successfully to Kubernetes'
        }
        failure {
            echo 'Pipeline failed - check test results'
        }
    }
}