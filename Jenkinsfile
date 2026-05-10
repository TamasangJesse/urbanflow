pipeline {
    agent any

    environment {
        ROOT_ENV                 = credentials('root-env')
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
                sh 'cp $ROOT_ENV .env'
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
                        sh 'docker compose run --rm --no-deps -v $(pwd)/services/user-service/tests:/app/tests user-service python -m pytest -v'
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/user-service/tests/reports/results.xml'
                        }
                    }
                }

                stage('Test: incident-report-service') {
                    steps {
                        sh 'docker compose run --rm --no-deps -v $(pwd)/services/incident-report-service/tests:/app/tests incident-report-service python -m pytest -v'
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/incident-report-service/tests/reports/results.xml'
                        }
                    }
                }

                stage('Test: notification-service') {
                    steps {
                        sh 'docker compose run --rm --no-deps -v $(pwd)/services/notification-service/tests:/app/tests notification-service python -m pytest -v'
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/notification-service/tests/reports/results.xml'
                        }
                    }
                }

                stage('Test: traffic-intelligence-service') {
                    steps {
                        sh 'docker compose run --rm --no-deps -v $(pwd)/services/traffic-intelligence-service/tests:/app/tests traffic-intelligence-service python -m pytest -v'
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/traffic-intelligence-service/tests/reports/results.xml'
                        }
                    }
                }

                stage('Test: api-gateway') {
                    steps {
                        sh 'docker compose run --rm --no-deps -v $(pwd)/services/api-gateway/tests:/app/tests api-gateway python -m pytest -v'
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/api-gateway/tests/reports/results.xml'
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