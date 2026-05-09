pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'Pulling latest code from GitHub...'
                checkout scm
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
                        sh '''
                            docker compose run --rm user-service \
                                python -m pytest tests/ \
                                --cov=app \
                                --cov-report=xml \
                                --junitxml=tests/test-results/results.xml -v
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/user-service/tests/test-results/*.xml'
                        }
                    }
                }

                stage('Test: incident-report-service') {
                    steps {
                        sh '''
                            docker compose run --rm incident-report-service \
                                python -m pytest tests/ \
                                --cov=app \
                                --cov-report=xml \
                                --junitxml=tests/test-results/results.xml -v
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/incident-report-service/tests/test-results/*.xml'
                        }
                    }
                }

                stage('Test: notification-service') {
                    steps {
                        sh '''
                            docker compose run --rm notification-service \
                                python -m pytest tests/ \
                                --cov=app \
                                --cov-report=xml \
                                --junitxml=tests/test-results/results.xml -v
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/notification-service/tests/test-results/*.xml'
                        }
                    }
                }

                stage('Test: traffic-intelligence-service') {
                    steps {
                        sh '''
                            docker compose run --rm traffic-intelligence-service \
                                python -m pytest tests/ \
                                --cov=app \
                                --cov-report=xml \
                                --junitxml=tests/test-results/results.xml -v
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/traffic-intelligence-service/tests/test-results/*.xml'
                        }
                    }
                }

                stage('Test: api-gateway') {
                    steps {
                        sh '''
                            docker compose run --rm api-gateway \
                                python -m pytest tests/ \
                                --cov=app \
                                --cov-report=xml \
                                --junitxml=tests/test-results/results.xml -v
                        '''
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
                sh '''
                    docker compose down
                    docker compose up -d
                '''
            }
        }

    }

    post {
        success {
            echo '✅ UrbanFlow deployed successfully'
        }
        failure {
            echo '❌ Pipeline failed - check test results'
        }
        always {
            echo "🏁 Pipeline finished on branch: ${env.BRANCH_NAME}"
            sh 'docker compose down || true'
        }
    }

}




