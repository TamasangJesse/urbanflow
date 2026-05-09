pipeline {
    agent any

    environment {
        USER_SERVICE_ENV         = credentials('user-service-env')
        INCIDENT_SERVICE_ENV     = credentials('incident-report-service-env')
        NOTIFICATION_SERVICE_ENV = credentials('notification-service-env')
        TRAFFIC_SERVICE_ENV      = credentials('traffic-intelligence-service-env')
        API_GATEWAY_ENV          = credentials('api-gateway-env')
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
                sh 'cp $USER_SERVICE_ENV services/user-service/.env'
                sh 'cp $INCIDENT_SERVICE_ENV services/incident-report-service/.env'
                sh 'cp $NOTIFICATION_SERVICE_ENV services/notification-service/.env'
                sh 'cp $TRAFFIC_SERVICE_ENV services/traffic-intelligence-service/.env'
                sh 'cp $API_GATEWAY_ENV services/api-gateway/.env'
            }
        }

        stage('Build') {
            steps {
                echo 'Building all Docker images...'
                sh 'docker compose build'
            }
        }

        stage('Test') {
            parallel {

                stage('Test: user-service') {
                    steps {
                        sh 'docker compose run --rm user-service python -m pytest tests/ --cov=app --cov-report=xml --junitxml=tests/test-results/results.xml -v'
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/user-service/tests/test-results/*.xml'
                        }
                    }
                }

                stage('Test: incident-report-service') {
                    steps {
                        sh 'docker compose run --rm incident-report-service python -m pytest tests/ --cov=app --cov-report=xml --junitxml=tests/test-results/results.xml -v'
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/incident-report-service/tests/test-results/*.xml'
                        }
                    }
                }

                stage('Test: notification-service') {
                    steps {
                        sh 'docker compose run --rm notification-service python -m pytest tests/ --cov=app --cov-report=xml --junitxml=tests/test-results/results.xml -v'
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/notification-service/tests/test-results/*.xml'
                        }
                    }
                }

                stage('Test: traffic-intelligence-service') {
                    steps {
                        sh 'docker compose run --rm traffic-intelligence-service python -m pytest tests/ --cov=app --cov-report=xml --junitxml=tests/test-results/results.xml -v'
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/traffic-intelligence-service/tests/test-results/*.xml'
                        }
                    }
                }

                stage('Test: api-gateway') {
                    steps {
                        sh 'docker compose run --rm api-gateway python -m pytest tests/ --cov=app --cov-report=xml --junitxml=tests/test-results/results.xml -v'
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/api-gateway/tests/test-results/*.xml'
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
                echo 'Deploying UrbanFlow to production...'
                sh 'docker compose down'
                sh 'docker compose up -d'
            }
        }

    }

    post {
        success {
            echo 'UrbanFlow deployed successfully'
        }
        failure {
            echo 'Pipeline failed - check test results'
        }
        always {
            echo "Pipeline finished on branch: ${env.BRANCH_NAME}"
            sh 'docker compose down || true'
        }
    }

}